"""Global configuration and environment settings."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# Load .env file
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# API Keys
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# Influencer Filtering Thresholds
TARGET_NICHE = os.getenv("TARGET_NICHE", "Tech & AI Tools")
MIN_FOLLOWERS = int(os.getenv("MIN_FOLLOWERS", 5000))
MAX_FOLLOWERS = int(os.getenv("MAX_FOLLOWERS", 100000))
MIN_ENGAGEMENT_RATE = float(os.getenv("MIN_ENGAGEMENT_RATE", 1.0))  # 1.0% benchmark
TARGET_INFLUENCERS_COUNT = int(os.getenv("MAX_INFLUENCERS_TARGET", 50))

# File paths for datasets
RAW_DATA_PATH = DATA_DIR / "raw_influencers.json"
FILTERED_DATA_PATH = DATA_DIR / "filtered_influencers.json"
OUTREACH_TRACKER_PATH = DATA_DIR / "outreach_tracker.csv"

# Sending settings
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SENDER_NAME = os.getenv("SENDER_NAME", "EDXSO Partnerships Team")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "partnerships@edxso.com")

