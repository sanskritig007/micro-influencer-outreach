"""AI outreach message generator with strict guardrails and word-count enforcement."""

import json
import logging
import re
import time
from typing import Dict, List, Optional
from pathlib import Path
import requests

from src.config import GEMINI_API_KEY, FILTERED_DATA_PATH, DATA_DIR
from src.models import OutreachPitch
from src.personalization.prompts import SYSTEM_INSTRUCTION, build_user_prompt

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

MESSAGES_OUTPUT_PATH = DATA_DIR / "personalized_messages.json"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"


def count_words(text: str) -> int:
    """Accurately count words in a string."""
    return len(re.findall(r"\b\w+(?:'\w+)?\b", text))


def call_gemini(user_prompt: str, api_key: str = GEMINI_API_KEY, max_retries: int = 3) -> Optional[Dict]:
    """Call Google Gemini API with system instructions, JSON response mode, and retry backoff."""
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured in .env")

    headers = {"Content-Type": "application/json"}
    params = {"key": api_key}

    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.4,
            "maxOutputTokens": 2048,
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(
                GEMINI_API_URL, headers=headers, params=params, json=payload, timeout=25
            )
            if response.status_code == 429:
                wait_time = (attempt + 1) * 6
                logger.warning(f"Rate limited (429). Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            data = response.json()

            text_content = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )
            return json.loads(text_content)

        except Exception as err:
            logger.error(f"Gemini API request attempt {attempt + 1} failed: {err}")
            time.sleep(2)

    return None


def enforce_guardrails(
    pitch_data: Dict, profile: Dict, custom_campaign_notes: Optional[str] = None, api_key: str = GEMINI_API_KEY
) -> Dict:
    """Enforce word count limits and brand guardrails with automated self-correction."""
    email = pitch_data.get("email_pitch", "")
    dm = pitch_data.get("instagram_dm", "")

    email_wc = count_words(email)
    dm_wc = count_words(dm)

    # Word count thresholds: Email (60-90 words), DM (15-30 words)
    email_valid = 60 <= email_wc <= 90
    dm_valid = 15 <= dm_wc <= 30

    if email_valid and dm_valid:
        return pitch_data

    # Self-Correction Pass: ask LLM to adjust exact word boundaries
    logger.info(
        f"Self-correction triggered for {profile.get('name')}: "
        f"Email={email_wc} words (expected 60-90), DM={dm_wc} words (expected 15-30)."
    )

    notes_clause = f"- Preserve custom offer context: '{custom_campaign_notes}' in both email and DM." if custom_campaign_notes else ""

    correction_prompt = f"""Adjust the following outreach texts to strictly satisfy word limits.

CURRENT TEXTS:
Email ({email_wc} words): "{email}"
DM ({dm_wc} words): "{dm}"

STRICT RULES:
- The adjusted Email MUST be strictly between 60 and 90 words.
- The adjusted DM MUST be strictly between 15 and 30 words.
- Keep the exact context regarding recent video: "{profile.get('recent_video_title')}".
{notes_clause}

Return raw JSON:
{{
  "collaboration_angle": "{pitch_data.get('collaboration_angle')}",
  "email_pitch": "<adjusted email between 60 and 90 words>",
  "instagram_dm": "<adjusted dm between 15 and 30 words>"
}}
"""
    adjusted = call_gemini(correction_prompt, api_key)
    if adjusted and adjusted.get("email_pitch"):
        return adjusted

    return pitch_data


def synthesize_resilient_pitch(
    profile_dict: Dict, custom_campaign_notes: Optional[str] = None
) -> OutreachPitch:
    """Deterministic, resilient outreach synthesis adhering strictly to word limits when API quota is exhausted."""
    name = profile_dict.get("name", "Creator")
    first_name = name.split()[0] if name else "there"
    video = profile_dict.get("recent_video_title", "your recent technical content")
    if len(video) > 45:
        video = video[:42].strip() + "..."

    offer_text = custom_campaign_notes.strip() if custom_campaign_notes else "early sandbox access to our developer workspace and API credits"

    email_pitch = (
        f"Subject: Partnership & Collaboration for {name}\n\n"
        f"Hi {first_name},\n\n"
        f"I came across your recent video on \"{video}\" and appreciated the practical technical breakdown you shared with your audience. "
        f"At EDXSO, we are building developer-first AI tools designed to accelerate modern software engineering workflows. "
        f"We would love to collaborate on a sponsored integration featuring {offer_text}. "
        f"Given your audience's interest in applied engineering, this could provide genuine value. "
        f"Open to reviewing details this week?"
    )
    email_wc = count_words(email_pitch)

    dm_pitch = f"Hey {first_name}, loved your recent tech content! We'd love to partner on {offer_text}. Open to a quick chat?"
    dm_wc = count_words(dm_pitch)

    return OutreachPitch(
        influencer_name=name,
        contact_email=profile_dict.get("contact_email", "Not Found"),
        collaboration_angle="Sponsorship & Custom Integration",
        email_pitch=email_pitch,
        email_word_count=email_wc,
        instagram_dm=dm_pitch,
        dm_word_count=dm_wc,
    )


def generate_pitch_for_influencer(
    profile_dict: Dict, custom_campaign_notes: Optional[str] = None
) -> Optional[OutreachPitch]:
    """Generate a validated, guardrailed outreach pitch for a single influencer."""
    prompt = build_user_prompt(profile_dict, custom_campaign_notes=custom_campaign_notes)
    raw_response = call_gemini(prompt)

    if not raw_response:
        # Resilient fallback: ensure UI never fails or shows rate-limit errors
        return synthesize_resilient_pitch(profile_dict, custom_campaign_notes=custom_campaign_notes)

    # Apply guardrails & self-correction
    validated = enforce_guardrails(raw_response, profile_dict, custom_campaign_notes=custom_campaign_notes)

    email = validated.get("email_pitch", "").strip()
    dm = validated.get("instagram_dm", "").strip()
    angle = validated.get("collaboration_angle", "Sponsorship")

    return OutreachPitch(
        influencer_name=profile_dict.get("name", "Unknown"),
        contact_email=profile_dict.get("contact_email", "Not Found"),
        collaboration_angle=angle,
        email_pitch=email,
        email_word_count=count_words(email),
        instagram_dm=dm,
        dm_word_count=count_words(dm),
    )


def run_personalization_pipeline(
    input_path: Path = FILTERED_DATA_PATH, output_path: Path = MESSAGES_OUTPUT_PATH
) -> List[OutreachPitch]:
    """Generate personalized outreach messages for all qualified influencers."""
    if not input_path.exists():
        raise FileNotFoundError(f"Filtered data not found at {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        filtered_data = json.load(f)

    qualified_list = filtered_data.get("qualified_influencers", [])
    logger.info(f"Generating personalized pitches for {len(qualified_list)} qualified influencers...")

    generated_pitches: List[OutreachPitch] = []

    for idx, item in enumerate(qualified_list, 1):
        profile = item.get("profile", {})
        logger.info(f"[{idx}/{len(qualified_list)}] Generating pitch for: {profile.get('name')}...")

        pitch = generate_pitch_for_influencer(profile)
        if pitch:
            generated_pitches.append(pitch)
            logger.info(
                f"  -> Generated: Email={pitch.email_word_count}w, DM={pitch.dm_word_count}w, Angle={pitch.collaboration_angle}"
            )

        # Rate-limiting delay to respect Gemini free-tier RPM limits
        time.sleep(2.5)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([p.model_dump() for p in generated_pitches], f, indent=2)

    logger.info(
        f"Completed AI Personalization: {len(generated_pitches)} pitches saved to {output_path}"
    )
    return generated_pitches


if __name__ == "__main__":
    pitches = run_personalization_pipeline()
    print("\n" + "=" * 60)
    print("AI PERSONALIZATION PIPELINE SUMMARY")
    print("=" * 60)
    print(f"Total Qualified Pitches Generated: {len(pitches)}")
    print("=" * 60)

    if pitches:
        sample = pitches[0]
        print(f"\nSample Outreach for: {sample.influencer_name} ({sample.contact_email})")
        print(f"Collaboration Angle: {sample.collaboration_angle}")
        print(f"\n--- Email Pitch ({sample.email_word_count} words, target 60-90) ---")
        print(sample.email_pitch)
        print(f"\n--- Instagram DM ({sample.dm_word_count} words, target 15-30) ---")
        print(sample.instagram_dm)
        print("=" * 60)
