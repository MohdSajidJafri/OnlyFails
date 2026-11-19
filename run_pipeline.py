#!/usr/bin/env python3
"""
Meme / Shorts Automation Pipeline — Master Orchestrator (OnlyFails).
Curates high-performing video clips from Reddit, applies advertiser-friendly safety checks,
renders 60 FPS vertical Shorts with creator header cards, and publishes to YouTube on schedule.
"""
from __future__ import annotations

import argparse
import sys
import threading
from pathlib import Path

# Force UTF-8 encoding on Windows standard output/error to prevent Unicode encoding crashes
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import config
from src.logger import (
    logger,
    log_stage_start,
    log_stage_finish,
    log_stage_error,
)
from src.reddit.client import get_random_reddit_post, save_processed_id, download_meme_video
from src.video.renderer import render_curator_short, _get_audio_duration
from src.narration.groq import generate_curator_caption
from src.upload import upload_short, check_scheduler_run
from src.upload.metadata import generate_optimized_metadata
from src.safety import ContentSafetyAnalyzer, log_rejected_post

# Global timeout for safety (30 minutes)
PIPELINE_TIMEOUT = 30 * 60


def clean_temp_files() -> None:
    """Clean intermediate temp files in output directory to save space."""
    logger.info("Cleaning up temporary render files...")
    for ext in ["*.ass", "*.mp3", "*.png"]:
        for f in config.OUTPUT_DIR.glob(ext):
            try:
                f.unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Could not delete temp file {f.name}: {e}")


def main() -> None:
    timer = threading.Timer(
        PIPELINE_TIMEOUT, 
        lambda: (
            log_stage_error("Global Pipeline", "Execution timed out", fatal=True),
            sys.exit(1)
        )
    )
    timer.daemon = True
    timer.start()

    try:
        ap = argparse.ArgumentParser(description="Reddit to Shorts Automation Pipeline")
        ap.add_argument("--no-upload", action="store_true", help="Skip YouTube upload phase")
        ap.add_argument("--force", action="store_true", help="Ignore scheduler slots, run immediately")
        ap.add_argument("--subreddit", default=None, help="Override subreddits to fetch from (comma-separated)")
        ap.add_argument("--privacy", default=config.YT_PRIVACY, choices=["public", "unlisted", "private"], help="YouTube video visibility")
        args = ap.parse_args()

        print("=" * 70)
        print("=== REDDIT TO SHORTS AUTOMATION PIPELINE ===")
        print("=" * 70)

        # ── Step 0: Scheduler Gatekeeping ────────────────────
        log_stage_start("Scheduler Check")
        if args.no_upload:
            should_run = True
            logger.info("Scheduler Check: Bypassed (--no-upload specified)")
        else:
            should_run = check_scheduler_run(force=args.force)
        log_stage_finish("Scheduler Check", {"should_run": should_run})
        
        if not should_run:
            print("\n[INFO] Pipeline run skipped by Scheduler. (Not inside an active time slot).")
            print("   Use '--force' to bypass this check.")
            sys.exit(0)

        if args.subreddit:
            config.SUBREDDITS = [s.strip() for s in args.subreddit.split(",") if s.strip()]

        # ── Step 1: Ingestion & Safety Verification Loop ─────
        safety_analyzer = ContentSafetyAnalyzer()
        post = None
        optimized_meta = None
        caption_title = ""
        meme_video_path = None

        max_attempts = 15
        attempted_ids = set()
        for attempt in range(1, max_attempts + 1):
            logger.info(f"Attempting post verification (Try {attempt}/{max_attempts})...")

            # Ingestion
            log_stage_start("Reddit Ingestion")
            post = get_random_reddit_post(exclude_ids=attempted_ids)
            if not post:
                error_msg = "No suitable Reddit posts found matching criteria"
                log_stage_error("Reddit Ingestion", error_msg, fatal=True)
                sys.exit(1)

            attempted_ids.add(post.id)
            log_stage_finish("Reddit Ingestion", {
                "id": post.id,
                "subreddit": post.subreddit,
                "title": post.title[:40] + "..."
            })

            # Download video asset
            try:
                meme_video_path = download_meme_video(post.media_url, post.id)
                if meme_video_path.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff'):
                    logger.warning(f"Post {post.id} rejected: Post is a static image, video required.")
                    continue

                try:
                    meme_duration = _get_audio_duration(meme_video_path)
                except Exception as ex:
                    logger.warning(f"Could not read video duration: {ex}. Defaulting to 10s.")
                    meme_duration = 10.0

                if meme_duration > config.MAX_MEME_DURATION:
                    logger.warning(f"Post {post.id} rejected: Duration {meme_duration:.1f}s > {config.MAX_MEME_DURATION:.1f}s")
                    continue
                if meme_duration < config.MIN_MEME_DURATION:
                    logger.warning(f"Post {post.id} rejected: Duration {meme_duration:.1f}s < {config.MIN_MEME_DURATION:.1f}s")
                    continue
            except Exception as e:
                log_stage_error("Reddit Ingestion", f"Failed to download video: {e}. Trying another post.")
                continue

            # Stage 1 Safety Check: After Ingestion
            safety_res = safety_analyzer.check_safety(
                title=post.title,
                body=post.selftext,
                image_path=meme_video_path,
                stage="After Ingestion"
            )

            if not safety_res["passed"]:
                logger.warning(f"Post {post.id} rejected at Stage 1 safety check. Reason: {safety_res['reason']}")
                log_rejected_post(
                    post_id=post.id,
                    subreddit=post.subreddit,
                    risk_score=safety_res["risk_score"],
                    category=", ".join(safety_res["categories_detected"]) or "safety_policy_violation",
                    reason=safety_res["reason"]
                )
                continue

            # Generate caption & metadata
            log_stage_start("Script Generation")
            caption_title = generate_curator_caption(post.title, post.subreddit)
            log_stage_finish("Script Generation", {"title": caption_title})

            optimized_meta = generate_optimized_metadata(
                post=post,
                narration="",
                llm_title=caption_title,
                llm_hook=caption_title,
                llm_summary=caption_title,
                llm_category="Entertainment",
                llm_content_tags=[]
            )

            logger.info(f"🎉 Post {post.id} passed safety validation! Proceeding to rendering.")
            break
        else:
            error_msg = f"Failed to ingest a safe Reddit post after {max_attempts} attempts."
            log_stage_error("Reddit Ingestion", error_msg, fatal=True)
            sys.exit(1)

        # ── Step 2: Video Rendering ──────────────────────────
        log_stage_start("Video Rendering")
        video_path = config.OUTPUT_DIR / "final_short.mp4"
        try:
            render_curator_short(
                meme_video_path=meme_video_path,
                output_path=video_path,
                title=caption_title or post.title,
                branding_text=config.BRANDING_TEXT,
                add_intro_outro=config.ADD_INTRO_OUTRO,
                subreddit=post.subreddit
            )
            log_stage_finish("Video Rendering", {"output_video": str(video_path)})
        except Exception as e:
            log_stage_error("Video Rendering", e, fatal=True)
            sys.exit(1)

        # ── Step 3: Database Update ──────────────────────────
        log_stage_start("Database Update")
        save_processed_id(post.id, post.subreddit)
        log_stage_finish("Database Update")

        # ── Step 4: YouTube Upload ───────────────────────────
        video_id = ""
        if not args.no_upload:
            log_stage_start("YouTube Upload")

            # Final Pre-Upload Safety Verification
            logger.info("Content Safety: Performing pre-upload validation...")
            safety_res = safety_analyzer.check_safety(
                yt_title=optimized_meta["title"],
                description=optimized_meta["description"],
                tags=optimized_meta["tags"],
                metadata={"category_id": optimized_meta["category_id"]},
                image_path=meme_video_path,
                stage="Before Upload"
            )

            if not safety_res["passed"]:
                logger.error(f"Post {post.id} REJECTED at pre-upload check! Reason: {safety_res['reason']}")
                log_rejected_post(
                    post_id=post.id,
                    subreddit=post.subreddit,
                    risk_score=safety_res["risk_score"],
                    category=", ".join(safety_res["categories_detected"]) or "safety_policy_violation",
                    reason=safety_res["reason"]
                )
                log_stage_error("YouTube Upload", f"Upload aborted: {safety_res['reason']}", fatal=True)
                sys.exit(1)

            video_id = upload_short(
                video_path=video_path,
                title=optimized_meta["title"],
                description=optimized_meta["description"],
                tags=optimized_meta["tags"],
                category_id=optimized_meta["category_id"],
                privacy=args.privacy
            )

            if video_id:
                log_stage_finish("YouTube Upload", {"video_id": video_id})
            else:
                log_stage_error("YouTube Upload", "Upload failed", fatal=True)
                sys.exit(1)
        else:
            log_stage_start("YouTube Upload")
            log_stage_finish("YouTube Upload", {"status": "skipped"})

        # Clean up intermediate render files
        clean_temp_files()

        print("\n[SUCCESS] PIPELINE SUCCESSFUL!")
        if video_id:
            print(f"   Published YouTube Short: https://www.youtube.com/shorts/{video_id}")
        print(f"   Video file saved to: {video_path}\n")

    finally:
        timer.cancel()


if __name__ == "__main__":
    main()
