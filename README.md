# 🎬 OnlyFails — Automated Reddit to YouTube Shorts Pipeline

A fully autonomous, production-grade Python pipeline that curates high-performing video clips from Reddit, renders viral 9:16 vertical Shorts at 60 FPS with sleek Twitter/X-style creator header cards, and publishes them to YouTube on an automated schedule.

Built to run seamlessly **locally** or **100% free 24/7 in the cloud** using GitHub Actions.

---

## 📑 Table of Contents

- [Overview & Visual Style](#-overview--visual-style)
- [Key Features](#-key-features)
- [Prerequisites](#-prerequisites)
- [Quickstart: Local Setup](#-quickstart-local-setup)
- [Credentials & API Setup](#-credentials--api-setup)
  - [1. YouTube Data API v3 (Required for Uploading)](#1-youtube-data-api-v3-required-for-uploading)
  - [2. Groq API (Optional: AI Captions & Curation)](#2-groq-api-optional-ai-captions)
  - [3. Gemini API (Optional: Multimodal Safety)](#3-gemini-api-optional-multimodal-safety)
- [Running the Pipeline](#-running-the-pipeline)
  - [CLI Flags & Options](#cli-flags--options)
- [Automated Cloud Deployment (GitHub Actions)](#-automated-cloud-deployment-github-actions)
- [Project Directory Structure](#-project-directory-structure)
- [Configuration Reference (.env Cheatsheet)](#-configuration-reference-env-cheatsheet)
- [🤖 Replicating for Another Niche or New Channel (Agent & Developer Guide)](#-replicating-for-another-niche-or-new-channel-agent--developer-guide)
- [Troubleshooting & FAQ](#-troubleshooting--faq)

---

## 🎨 Overview & Visual Style

The pipeline operates in **Curator Mode** (`CURATOR_MODE=True`), designed after top viral Short & Reel creators:

```text
┌───────────────────────────────────────────────┐
│               1080 x 1920 (9:16)              │
│            PURE WHITE BACKGROUND CANVAS       │
│                                               │
│   ┌───────────────────────────────────────┐   │
│   │ [Avatar] OnlyFails [✓ Verified (Blue)]│   │  <-- Dynamic Twitter/X-style
│   │          @onlyfail.s                  │   │      Creator Header Card
│   │                                       │   │
│   │ "Bro really doubted physics for a    │   │  <-- Clean post title / hook
│   │  second 😂"                           │   │      with native emoji support
│   └───────────────────────────────────────┘   │
│                                               │
│   ┌───────────────────────────────────────┐   │
│   │                                       │   │
│   │                                       │   │  <-- Original Reddit Video
│   │         ORIGINAL VIDEO MEME           │   │      (Scaled 1080px edge-to-edge,
│   │                                       │   │       original audio preserved)
│   │                                       │   │
│   └───────────────────────────────────────┘   │
│                                               │
│                                               │
└───────────────────────────────────────────────┘
```

* **Authentic Audio**: Preserves the original video's authentic sound rather than synthetic robot voiceovers.
* **Edge-to-Edge Video Framing**: Clips automatically scale to 1080px full width with centered vertical framing on a clean canvas.
* **Dynamic Header Card**: Pre-rendered via Pillow with high-resolution circular avatar masking, custom verified checkmark badge, and multi-line emoji-aware typography.

---

## 🚀 Key Features

* **Curator Mode (Default)**: Automatically curates funny fails and unexpected video clips, pairs them with punchy creator captions, and packages them into clean 9:16 60 FPS vertical video.
* **Lean, Zero-Bloat Architecture**: Completely decluttered of unused TTS, synthetic voiceovers, and gameplay backgrounds. Operates on just 9 core Python dependencies for near-instant GitHub Actions runner setup.
* **Fast & Resilient Ingestion**: Uses `curl-cffi` browser TLS impersonation, automatic Redlib proxy rotation, and direct Reddit CDN (Fastly) stream downloads. No Reddit developer credentials required.
* **2-Stage Advertiser Safety Guard**:
  1. *After Ingestion*: Scans post titles, selftext, and video frames using 14 comprehensive safety categories (violence, hate, harassment, self-harm, adult content, etc.) via local rule-based regex, with zero error spam if LLM keys are absent.
  2. *Before Upload*: Final advertiser-friendly policy validation on YouTube title, description, and tags before publishing.
* **Resumable YouTube OAuth2 Publishing**: Seamless chunked resumable upload script with automatic categorization (Entertainment), tags, and disclaimer inclusion.
* **Smart Scheduler & De-duplication**:
  * Prevents duplicate video uploads via `data/database/processed_reddit_posts.json`.
  * Enforces daily video limits (`MAX_VIDEOS_PER_DAY=4`) and designated upload hours (`09:00, 13:00, 17:00, 21:00 IST`).

---

## 💻 Prerequisites

1. **Python 3.10, 3.11, or 3.12**
2. **FFmpeg & FFprobe**: Required for video slicing, resizing, and rendering.
   * **Windows**: Bundled in `bin/` directory automatically, or install via `winget install Gyan.FFmpeg`.
   * **Ubuntu / Debian**: `sudo apt update && sudo apt install -y ffmpeg fonts-liberation`
   * **macOS**: `brew install ffmpeg`

---

## ⚡ Quickstart: Local Setup

### 1. Clone the Repository
```bash
git clone https://github.com/MohdSajidJafri/OnlyFails.git
cd OnlyFails
```

### 2. Create a Virtual Environment
```bash
# Windows:
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS:
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Create Your Environment Configuration
Copy `.env.example` into `.env`:
```bash
# Windows:
copy .env.example .env

# Linux / macOS:
cp .env.example .env
```

---

## 🔑 Credentials & API Setup

### 1. YouTube Data API v3 (Required for Uploading)

#### Step A: Create Google Cloud OAuth Credentials
1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (e.g., `OnlyFails Shorts Bot`).
3. In the sidebar, go to **APIs & Services** > **Library**, search for **YouTube Data API v3**, and click **Enable**.
4. Go to **APIs & Services** > **OAuth consent screen**:
   * Choose **External** and click **Create**.
   * Enter an App name (`OnlyFails Bot`) and your support email.
   * Under **Test Users**, click **+ Add Users** and enter the Google account email of your YouTube channel.
5. Go to **APIs & Services** > **Credentials**:
   * Click **+ Create Credentials** > **OAuth client ID**.
   * Application type: **Desktop app**.
   * Name: `OnlyFails Uploader`.
   * Click **Create**.
6. Copy your **Client ID** and **Client Secret** into your `.env`:
   ```dotenv
   YT_CLIENT_ID=your_client_id.apps.googleusercontent.com
   YT_CLIENT_SECRET_VALUE=your_client_secret
   ```

#### Step B: Generate the Refresh Token
Run the included helper script:
```bash
python get_refresh_token.py
```
* A browser window will open asking you to sign in with your Google account.
* Authorize the permissions.
* The script will capture the code, output your `YT_REFRESH_TOKEN`, and write it directly into your `.env` file.

---

### 2. Groq API (Optional: AI Captions)
The bot can use Groq to generate witty, viral one-line creator captions from Reddit post titles:
1. Get a free API key from [console.groq.com](https://console.groq.com/).
2. Add to `.env`:
   ```dotenv
   LLM_PROVIDER=groq
   GROQ_API_KEY=gsk_your_groq_api_key_here
   LLM_MODEL="qwen/qwen3.8-27b"
   ```
*(If left empty, the bot cleanly uses the original Reddit title).*

---

### 3. Gemini API (Optional: Multimodal Safety)
For advanced visual safety moderation and watermark detection:
1. Obtain an API key from [Google AI Studio](https://aistudio.google.com/).
2. Add to `.env`:
   ```dotenv
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

---

## 🎮 Running the Pipeline

### 1. Dry Run (Render Locally, Skip Upload)
Ingest a live video from Reddit, render the 1080×1920 Short locally, and skip YouTube upload:
```bash
python run_pipeline.py --force --no-upload
```
Rendered video is saved at `data/output/final_short.mp4`.

### 2. Live Run (Render & Upload Immediately)
Bypasses the schedule check and uploads directly to YouTube:
```bash
python run_pipeline.py --force
```

### 3. Scheduled Execution (Production Mode)
Checks if the current time matches `UPLOAD_SCHEDULE_TIMES` (`09:00, 13:00, 17:00, 21:00`) and verifies that the daily upload limit (`MAX_VIDEOS_PER_DAY=4`) is not exceeded:
```bash
python run_pipeline.py
```

### CLI Flags & Options

| Flag | Description | Example |
|---|---|---|
| `--force` | Bypasses scheduler time-slot check and executes immediately. | `python run_pipeline.py --force` |
| `--no-upload` | Renders video locally without uploading to YouTube. | `python run_pipeline.py --force --no-upload` |
| `--subreddit <name>` | Overrides `.env` and fetches from a specific subreddit. | `python run_pipeline.py --force --subreddit Unexpected` |
| `--privacy <visibility>`| Sets YouTube video privacy (`public`, `unlisted`, `private`). | `python run_pipeline.py --force --privacy unlisted` |

---

## ☁️ Automated Cloud Deployment (GitHub Actions)

This repository includes a streamlined GitHub Actions workflow ([.github/workflows/daily_shorts.yml](.github/workflows/daily_shorts.yml)) that runs 4 times daily (09:00, 13:00, 17:00, and 21:00 IST) on a free GitHub-hosted runner.

### How to Enable:
1. Go to your repository on GitHub: **Settings** > **Secrets and variables** > **Actions**.
2. Add the following **Repository secrets**:
   * `YT_CLIENT_ID`
   * `YT_CLIENT_SECRET_VALUE`
   * `YT_REFRESH_TOKEN`
   * `GROQ_API_KEY` *(Optional: AI caption generation)*
   * `GEMINI_API_KEY` *(Optional: Multimodal vision safety scan)*
3. **Grant Write Permissions for Database Persistence**:
   * Go to **Settings** > **Actions** > **General**.
   * Under **Workflow permissions**, select **Read and write permissions**.
   * Click **Save**.
4. Test run: Go to the **Actions** tab > click **OnlyFails Shorts Bot** > click **Run workflow**.

---

## 📂 Project Directory Structure

```text
OnlyFails/
├── .github/
│   └── workflows/
│       └── daily_shorts.yml          # Automated 4x/day GitHub Actions runner
├── data/
│   ├── assets/                       # Channel profile picture / logo
│   │   └── OnlyFails Cyan Wing Logo.png
│   ├── database/                     # Deduplication and history tracking
│   │   ├── processed_reddit_posts.json
│   │   ├── subreddit_history.json
│   │   ├── upload_history.json
│   │   └── rejected_posts.json
│   ├── output/                       # Destination for final rendered MP4s
│   └── raw/                          # Downloaded temporary video memes
├── src/
│   ├── logger.py                     # Unified console & file logging
│   ├── narration/                    # Punchy viral caption generator (local heuristics + optional Groq)
│   ├── reddit/                       # Reddit crawling, Redlib proxy rotation, & direct CDN video muxing
│   ├── safety/                       # 2-stage policy & keyword safety analyzer (14 categories)
│   ├── upload/                       # YouTube Data API v3 resumable uploader & scheduler
│   └── video/                        # High-performance 60 FPS FFmpeg rendering engine & creator card generator
├── .env.example                      # Template for environment configuration
├── config.py                         # Centralized configuration reader
├── get_refresh_token.py              # OAuth2 helper to generate YouTube refresh token
├── requirements.txt                  # Slim 9-package Python dependencies
└── run_pipeline.py                   # Master pipeline orchestrator
```

---

## ⚙️ Configuration Reference (.env Cheatsheet)

| Variable | Default | Description |
|---|---|---|
| `CURATOR_MODE` | `True` | Direct video curation mode with original audio preserved |
| `SUBREDDITS` | `Whatcouldgowrong, Unexpected, AccidentalSlapStick` | Target subreddits for content ingestion |
| `PROFILE_PICTURE_PATH`| `"data/assets/OnlyFails Cyan Wing Logo.png"` | Path to your channel avatar image |
| `CHANNEL_DISPLAY_NAME`| `"OnlyFails"` | Display name shown on Creator Header Card |
| `CHANNEL_HANDLE` | `"@onlyfail.s"` | Handle shown below display name |
| `BADGE_COLOR` | `"#1DA1F2"` | Hex color of verified badge (Twitter/X Blue) |
| `BACKGROUND_COLOR` | `"#FFFFFF"` | Background canvas hex color |
| `MAX_MEME_DURATION` | `59` | Max allowed video length in seconds |
| `MIN_MEME_DURATION` | `3` | Min allowed video length in seconds |
| `MAX_VIDEOS_PER_DAY` | `4` | Maximum daily upload limit |
| `UPLOAD_SCHEDULE_TIMES`| `09:00, 13:00, 17:00, 21:00` | Designated daily upload windows (IST) |
| `YOUTUBE_PRIVACY` | `public` | YouTube visibility (`public`, `unlisted`, `private`) |

---

## 🤖 Replicating for Another Niche or New Channel (Agent & Developer Guide)

This architecture is completely modular. If you (or an AI assistant) want to spin up a new channel for a different niche (e.g. **Technology**, **Gaming**, **Oddly Satisfying**, **Wholesome**, or **Animals**), follow this exact checklist:

### Step 1: Change Target Subreddits
In your `.env`:
```dotenv
# Example for a Tech Channel:
SUBREDDITS=technology, gadgets, damnthatsinteresting, specializedtools

# Example for a Gaming Channel:
SUBREDDITS=gaming, GamePhysics, livestreamfail

# Example for an Oddly Satisfying Channel:
SUBREDDITS=oddlysatisfying, Satisfyingasfuck, BeAmazed
```

### Step 2: Swap the Profile Picture / Logo
1. Put your new channel image (PNG or JPG) into `data/assets/` (e.g. `data/assets/TechDaily Logo.png`).
2. Update `.env`:
```dotenv
PROFILE_PICTURE_PATH="data/assets/TechDaily Logo.png"
```

### Step 3: Update Channel Identity & Colors
In `.env`:
```dotenv
CHANNEL_DISPLAY_NAME="TechDaily"
CHANNEL_HANDLE="@techdaily.io"
BADGE_COLOR="#1DA1F2"        # #1DA1F2 (Blue), #00FF66 (Green), #FB0101 (Red), or #FFD700 (Gold)
BACKGROUND_COLOR="#FFFFFF"   # #FFFFFF (Clean White) or #000000 (OLED Dark Mode)
```

### Step 4: Update SEO Tags & Disclaimers
In `.env`:
```dotenv
METADATA_TRENDING_TAGS=tech, technology, gadgets, innovation, future, shorts
METADATA_DISCLAIMER=Curated tech clips and innovations from Reddit.
```

### Step 5: Connect the New YouTube Channel
1. In Google Cloud Console, add the new channel's email to **Test Users**.
2. Run `python get_refresh_token.py` and authenticate with the new channel.
3. Update `YT_REFRESH_TOKEN` in `.env` (and in your new repo's GitHub Secrets).

### Step 6: Clear History Databases
If forking the repo for a brand new channel, reset the database files:
```powershell
Set-Content -Path data/database/processed_reddit_posts.json -Value "[]"
Set-Content -Path data/database/upload_history.json -Value "[]"
Set-Content -Path data/database/rejected_posts.json -Value "[]"
Set-Content -Path data/database/subreddit_history.json -Value "{}"
```

Once these steps are done, the entire pipeline immediately curates and publishes for the new niche with zero code refactoring!

---

## ❓ Troubleshooting & FAQ

### 1. `FileNotFoundError: 'ffmpeg'` or `'ffprobe'`
* On Windows, ensure the `bin/` directory containing `ffmpeg.exe` and `ffprobe.exe` is present in the repository root. `config.py` automatically injects `bin/` into the system PATH at runtime.

### 2. HTTP 403 Forbidden when downloading Reddit videos
* Reddit occasionally restricts datacenter IPs.
* The codebase uses `curl-cffi` to mimic real browser TLS fingerprints and rotates through live Redlib proxy mirrors (e.g. `redlib.zanity.net`) automatically.

### 3. YouTube Upload Token Expired (`invalid_grant`)
* If your Google Cloud project is in **Testing** status, refresh tokens expire every 7 days.
* **To make your token permanent**:
  1. In Google Cloud Console, navigate to **APIs & Services** > **OAuth consent screen**.
  2. Click **Publish App** to switch from "Testing" to "In Production".
  3. Re-run `python get_refresh_token.py` once to get a permanent token.

### 4. Scheduler skips execution
* If running manually, always add `--force`:
  ```bash
  python run_pipeline.py --force
  ```

---

## ⚖️ License & Disclaimer

Built for autonomous content creation and curation. Ensure compliance with [Reddit's API & Data Terms](https://www.reddit.com/wiki/api-terms) and [YouTube Community Guidelines](https://www.youtube.com/howyoutubeworks/policies/community-guidelines/) when publishing curated media.
