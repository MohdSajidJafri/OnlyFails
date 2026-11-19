"""
Central configuration for the Reddit to Shorts Automation Pipeline (OnlyFails).
Reads from .env file, provides clean and direct defaults for 60 FPS video curation.
"""
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent

# Load local environment file
load_dotenv(ROOT / ".env")

# Ensure bundled ffmpeg/ffprobe binaries are on PATH
BIN_DIR = ROOT / "bin"
if BIN_DIR.exists():
    os.environ["PATH"] = str(BIN_DIR) + os.pathsep + os.environ.get("PATH", "")


def _env(key: str, default: str = "") -> str:
    """Helper to fetch config from environment, stripping leading/trailing whitespace and quotes."""
    val = os.environ.get(key)
    if val is None or val.strip() == "":
        return default
    return val.strip().strip('"').strip("'").strip()


def _env_bool(key: str, default: bool = False) -> bool:
    """Helper to fetch boolean config from environment."""
    val = os.environ.get(key)
    if val is None or val.strip() == "":
        return default
    return val.strip().lower() in ("true", "1", "yes", "on")


# ── Directories ──────────────────────────────────────────────
DATA_DIR_NAME = _env("DATA_DIR_NAME", "data")
RAW_DIR = ROOT / DATA_DIR_NAME / "raw"                 # Downloaded temporary video memes
OUTPUT_DIR = ROOT / DATA_DIR_NAME / "output"           # Rendered assets/shorts
CACHE_DIR = ROOT / DATA_DIR_NAME / "cache"             # Session tokens/archives
DB_DIR = ROOT / DATA_DIR_NAME / "database"             # Deduplication databases
ASSETS_DIR = ROOT / DATA_DIR_NAME / "assets"           # Channel logo / profile images

for d in [RAW_DIR, OUTPUT_DIR, CACHE_DIR, DB_DIR, ASSETS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Database Files
HISTORY_FILE = DB_DIR / "processed_reddit_posts.json"
UPLOAD_HISTORY_FILE = DB_DIR / "upload_history.json"

# ── Reddit Ingestion Settings ────────────────────────────────
SUBREDDITS = [
    s.strip()
    for s in _env(
        "SUBREDDITS",
        "Whatcouldgowrong, Unexpected, AccidentalSlapStick",
    ).split(",")
    if s.strip()
]

# Configurable selection weights for each subreddit
SUBREDDIT_WEIGHTS = {}
for s in SUBREDDITS:
    SUBREDDIT_WEIGHTS[s] = 1.0

_preferred_weights = {
    "Whatcouldgowrong": 5.0,
    "Unexpected": 5.0,
    "AccidentalSlapStick": 5.0,
    "memes": 3.0,
    "dankmemes": 3.0,
}
for s, w in _preferred_weights.items():
    if s in SUBREDDIT_WEIGHTS:
        SUBREDDIT_WEIGHTS[s] = float(_env(f"SUBREDDIT_WEIGHT_{s.upper()}", str(w)))

REDDIT_SORT = _env("REDDIT_SORT", "best")  # best, top, hot, rising, new
REDDIT_TIME_FILTER = _env("REDDIT_TIME_FILTER", "week")  # day, week, month, year, all
REDDIT_MIN_SCORE = int(_env("REDDIT_MIN_SCORE", "100"))
REDDIT_MIN_COMMENTS = int(_env("REDDIT_MIN_COMMENTS", "10"))
REDDIT_FILTER_NSFW = _env_bool("REDDIT_FILTER_NSFW", True)
REDDIT_FILTER_DELETED = _env_bool("REDDIT_FILTER_DELETED", True)
REDDIT_FILTER_PINNED = _env_bool("REDDIT_FILTER_PINNED", True)
REDDIT_FILTER_CROSSPOSTS = _env_bool("REDDIT_FILTER_CROSSPOSTS", True)
ONLY_VIDEOS = _env_bool("ONLY_VIDEOS", True)
ONLY_REDDIT_HOSTED = _env_bool("ONLY_REDDIT_HOSTED", True)

# Optional Reddit API Credentials (uses anonymous feeds / Redlib rotation by default)
REDDIT_CLIENT_ID = _env("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = _env("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = _env("REDDIT_USER_AGENT", "OnlyFailsBot/1.0")

# ── Optional AI Curation (Groq) ──────────────────────────────
GROQ_API_KEY = _env("GROQ_API_KEY", "")
GEMINI_API_KEY = _env("GEMINI_API_KEY", "")
LLM_MODEL = _env("LLM_MODEL", "qwen/qwen3.8-27b")
LLM_PROVIDER = _env("LLM_PROVIDER", "groq")

# ── Video Render Settings ────────────────────────────────────
RENDER_FPS = int(_env("RENDER_FPS", "60"))
RENDER_WIDTH = 1080
RENDER_HEIGHT = 1920
CAPTION_FONT = _env("CAPTION_FONT", "Impact")
OVERLAY_PROGRESS_BAR = _env_bool("OVERLAY_PROGRESS_BAR", False)
OVERLAY_BACKGROUND_BLUR = _env_bool("OVERLAY_BACKGROUND_BLUR", False)
OVERLAY_PROFILE_ICON = _env_bool("OVERLAY_PROFILE_ICON", True)
OVERLAY_SUBREDDIT_TAG = _env_bool("OVERLAY_SUBREDDIT_TAG", True)

# ── Curator Mode Video Settings ──────────────────────────────
CURATOR_MODE = _env_bool("CURATOR_MODE", True)
MAX_MEME_DURATION = float(_env("MAX_MEME_DURATION", "59.0"))
MIN_MEME_DURATION = float(_env("MIN_MEME_DURATION", "3.0"))
REJECT_WATERMARKS = _env_bool("REJECT_WATERMARKS", False)
BRANDING_TEXT = _env("BRANDING_TEXT", "")
ADD_INTRO_OUTRO = _env_bool("ADD_INTRO_OUTRO", False)
FIT_CLIP_WIDTH = _env_bool("FIT_CLIP_WIDTH", True)

# ── Creator Card Branding (OnlyFails) ─────────────────────────
PROFILE_PICTURE_PATH = ROOT / _env("PROFILE_PICTURE_PATH", f"{DATA_DIR_NAME}/assets/OnlyFails Cyan Wing Logo.png")
CHANNEL_DISPLAY_NAME = _env("CHANNEL_DISPLAY_NAME", "OnlyFails")
CHANNEL_HANDLE = _env("CHANNEL_HANDLE", "@onlyfail.s")
BADGE_COLOR = _env("BADGE_COLOR", "#1DA1F2")           # Blue verified tick circle
BACKGROUND_COLOR = _env("BACKGROUND_COLOR", "#FFFFFF")  # Pure white background canvas

# ── Content Safety Settings ──────────────────────────────────
ENABLE_CONTENT_SAFETY = _env_bool("ENABLE_CONTENT_SAFETY", True)
SAFETY_MODE = _env("SAFETY_MODE", "standard").lower().strip()  # standard, strict, lenient
MAX_ALLOWED_RISK = _env("MAX_ALLOWED_RISK", "low").lower().strip()

# ── YouTube Upload Settings ──────────────────────────────────
YT_CLIENT_ID = _env("YT_CLIENT_ID", _env("YT_MEME_CLIENT_ID"))
YT_CLIENT_SECRET = _env("YT_CLIENT_SECRET_VALUE", _env("YT_MEME_CLIENT_SECRET_VALUE"))
YT_REFRESH_TOKEN = _env("YT_REFRESH_TOKEN", _env("YT_MEME_REFRESH_TOKEN"))
YT_PRIVACY = _env("YOUTUBE_PRIVACY", "public")
YOUTUBE_CATEGORY_ID = _env("YOUTUBE_CATEGORY_ID", "24")  # 24 = Entertainment

METADATA_MENTIONS = _env("METADATA_MENTIONS", "")
METADATA_TRENDING_TAGS = _env(
    "METADATA_TRENDING_TAGS",
    "whatcouldgowrong, wcgw, unexpected, instantregret, instantkarma, fail, fails, viral, shorts",
)
METADATA_DISCLAIMER = _env("METADATA_DISCLAIMER", "Curated funny fail & unexpected clips from Reddit.")

# ── Scheduler & Limits ───────────────────────────────────────
MAX_VIDEOS_PER_DAY = int(_env("MAX_VIDEOS_PER_DAY", "4"))
UPLOAD_SCHEDULE_TIMES = [
    t.strip()
    for t in _env("UPLOAD_SCHEDULE_TIMES", "09:00, 13:00, 17:00, 21:00").split(",")
    if t.strip()
]
