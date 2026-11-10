"""YouTube creator discovery and metrics extraction."""

import json
import logging
import re
from typing import Dict, List, Optional, Tuple
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.config import (
    YOUTUBE_API_KEY,
    RAW_DATA_PATH,
    TARGET_NICHE,
)
from src.models import InfluencerProfile

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Search queries designed to discover Tech & AI micro-influencers
DEFAULT_SEARCH_QUERIES = [
    "AI tools tutorial",
    "Python automation projects",
    "Machine Learning developer",
    "tech gadgets review",
    "coding workflows AI",
    "software engineering tips",
]


def get_youtube_client():
    """Initialize and return the YouTube Data API client."""
    if not YOUTUBE_API_KEY:
        raise ValueError("YOUTUBE_API_KEY is not set. Please check your .env file.")
    return build("youtube", "v3", developerKey=YOUTUBE_API_KEY)


def extract_email(text: str) -> str:
    """Extract the first valid email address from bio text, or return 'Not Found'."""
    if not text:
        return "Not Found"

    email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    matches = re.findall(email_pattern, text)

    for match in matches:
        cleaned = match.strip(".,;:()")
        # Filter out common false positives like file extensions
        if not cleaned.endswith((".png", ".jpg", ".jpeg", ".webp")):
            return cleaned.lower()

    return "Not Found"


def extract_content_themes(text: str) -> List[str]:
    """Identify relevant content themes based on bio keywords."""
    theme_keywords = {
        "AI & LLMs": ["ai", "llm", "gpt", "openai", "claude", "gemini", "agent"],
        "Python & Coding": ["python", "code", "coding", "programming", "software", "developer"],
        "Automation": ["automation", "workflow", "bots", "scraping", "productivity"],
        "Tech Reviews": ["review", "gadget", "hardware", "unboxing", "setup"],
        "Machine Learning": ["machine learning", "deep learning", "data science", "neural"],
        "DevOps & Cloud": ["cloud", "docker", "aws", "kubernetes", "devops"],
    }

    lowered = text.lower()
    themes = [theme for theme, words in theme_keywords.items() if any(w in lowered for w in words)]
    return themes if themes else ["Tech & AI Content"]


def search_channel_ids(youtube, queries: List[str], target_channels: int = 70) -> List[str]:
    """Search YouTube for channels matching our target niche keywords."""
    discovered_ids = []

    logger.info(f"Starting channel discovery across {len(queries)} search queries...")
    for query in queries:
        if len(discovered_ids) >= target_channels:
            break

        try:
            request = youtube.search().list(
                q=query,
                type="channel",
                part="snippet",
                maxResults=25,
            )
            response = request.execute()

            for item in response.get("items", []):
                channel_id = item["snippet"]["channelId"]
                if channel_id not in discovered_ids:
                    discovered_ids.append(channel_id)

            logger.info(f"Query '{query}': Found {len(response.get('items', []))} channels. Total unique so far: {len(discovered_ids)}")

        except HttpError as err:
            logger.error(f"YouTube search error for query '{query}': {err}")
            break

    return discovered_ids


def get_channel_details_batch(youtube, channel_ids: List[str]) -> List[Dict]:
    """Fetch channel metadata and statistics in batches of 50 to optimize API quota."""
    all_channels = []
    batch_size = 50

    for i in range(0, len(channel_ids), batch_size):
        batch = channel_ids[i:i + batch_size]
        try:
            request = youtube.channels().list(
                id=",".join(batch),
                part="snippet,statistics,contentDetails",
            )
            response = request.execute()
            all_channels.extend(response.get("items", []))
        except HttpError as err:
            logger.error(f"Error fetching channel details batch: {err}")

    logger.info(f"Successfully retrieved metadata for {len(all_channels)} channels.")
    return all_channels


def get_recent_video_metrics(
    youtube, uploads_playlist_id: str, subscriber_count: int
) -> Tuple[float, Optional[str], Optional[str]]:
    """Fetch stats from recent videos to compute engagement rate and recent content context."""
    if not uploads_playlist_id or subscriber_count <= 0:
        return 0.0, None, None

    try:
        # Get latest 5 video IDs from uploads playlist
        playlist_request = youtube.playlistItems().list(
            playlistId=uploads_playlist_id,
            part="contentDetails",
            maxResults=5,
        )
        playlist_response = playlist_request.execute()
        video_ids = [
            item["contentDetails"]["videoId"]
            for item in playlist_response.get("items", [])
        ]

        if not video_ids:
            return 0.0, None, None

        # Fetch video statistics and snippets in a single batch call
        videos_request = youtube.videos().list(
            id=",".join(video_ids),
            part="snippet,statistics",
        )
        videos_response = videos_request.execute()
        video_items = videos_response.get("items", [])

        if not video_items:
            return 0.0, None, None

        total_likes = 0
        total_comments = 0
        for video in video_items:
            stats = video.get("statistics", {})
            total_likes += int(stats.get("likeCount", 0))
            total_comments += int(stats.get("commentCount", 0))

        # Scientific engagement calculation across recent videos
        avg_likes = total_likes / len(video_items)
        avg_comments = total_comments / len(video_items)
        engagement_rate = round(((avg_likes + avg_comments) / subscriber_count) * 100, 2)

        # Most recent video details for personalization context
        latest_video = video_items[0]
        recent_title = latest_video.get("snippet", {}).get("title")
        recent_description = latest_video.get("snippet", {}).get("description", "")[:200]

        return engagement_rate, recent_title, recent_description

    except HttpError as err:
        logger.warning(f"Could not fetch video metrics: {err}")
        return 0.0, None, None


def fetch_influencers(target_count: int = 55) -> List[InfluencerProfile]:
    """Execute the full discovery pipeline and return discovered influencer profiles."""
    youtube = get_youtube_client()

    # Step 1: Discover channel IDs
    channel_ids = search_channel_ids(
        youtube, DEFAULT_SEARCH_QUERIES, target_channels=target_count + 25
    )

    # Step 2: Fetch batch channel metadata
    channel_items = get_channel_details_batch(youtube, channel_ids)

    # Step 3: Parse and enrich each profile
    discovered_profiles: List[InfluencerProfile] = []

    logger.info("Extracting metrics and recent video engagement...")
    for item in channel_items:
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        content_details = item.get("contentDetails", {})

        # Skip channels with hidden subscriber counts
        if statistics.get("hiddenSubscriberCount", False):
            continue

        subscriber_count = int(statistics.get("subscriberCount", 0))
        channel_id = item.get("id", "")
        title = snippet.get("title", "Unknown Creator")
        description = snippet.get("description", "")
        custom_url = snippet.get("customUrl", "")

        profile_url = (
            f"https://www.youtube.com/{custom_url}"
            if custom_url
            else f"https://www.youtube.com/channel/{channel_id}"
        )

        uploads_playlist = (
            content_details.get("relatedPlaylists", {}).get("uploads", "")
        )

        # Calculate engagement rate and fetch recent video context
        engagement_rate, recent_title, recent_desc = get_recent_video_metrics(
            youtube, uploads_playlist, subscriber_count
        )

        # Extract email and content themes
        contact_email = extract_email(description)
        themes = extract_content_themes(f"{title} {description} {recent_title or ''}")

        profile = InfluencerProfile(
            channel_id=channel_id,
            name=title,
            platform="YouTube",
            profile_url=profile_url,
            follower_count=subscriber_count,
            engagement_rate=engagement_rate,
            niche=TARGET_NICHE,
            content_themes=themes,
            contact_email=contact_email,
            secondary_handles=custom_url or None,
            recent_video_title=recent_title,
            recent_video_description=recent_desc,
        )
        discovered_profiles.append(profile)

        if len(discovered_profiles) >= target_count:
            break

    # Step 4: Save raw discovered data to disk
    RAW_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RAW_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump([p.model_dump() for p in discovered_profiles], f, indent=2)

    logger.info(f"Saved {len(discovered_profiles)} discovered profiles to {RAW_DATA_PATH}")
    return discovered_profiles


if __name__ == "__main__":
    fetch_influencers(target_count=55)

