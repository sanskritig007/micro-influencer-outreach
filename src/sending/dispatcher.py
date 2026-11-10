"""Outreach delivery dispatcher supporting Safe Simulation, SMTP, and Instagram DM workflows."""

import json
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List, Optional

from src.config import (
    DATA_DIR,
    FILTERED_DATA_PATH,
    OUTREACH_TRACKER_PATH,
    SENDER_EMAIL,
    SENDER_NAME,
    SMTP_HOST,
    SMTP_PASS,
    SMTP_PORT,
    SMTP_USER,
)
from src.sending.tracker import is_already_contacted, log_outreach_record

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

MESSAGES_INPUT_PATH = DATA_DIR / "personalized_messages.json"


def send_real_email(
    to_email: str,
    subject: str,
    body: str,
    sender_name: str = SENDER_NAME,
    sender_email: str = SENDER_EMAIL,
    smtp_host: str = SMTP_HOST,
    smtp_port: int = SMTP_PORT,
    smtp_user: str = SMTP_USER,
    smtp_pass: str = SMTP_PASS,
) -> bool:
    """Send an email via standard SMTP."""
    if not smtp_user or not smtp_pass:
        raise ValueError(
            "SMTP credentials are not configured in .env. Please configure SMTP or use simulation mode."
        )

    msg = MIMEMultipart()
    msg["From"] = f"{sender_name} <{sender_email}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)

    return True


def dispatch_email_pitch(
    influencer_name: str,
    email: str,
    channel_id: str,
    collaboration_angle: str,
    email_pitch: str,
    simulate: bool = True,
) -> Dict:
    """Dispatch a single email pitch with deduplication and state logging."""
    # 1. Check if email is available
    if not email or email.lower() == "not found":
        log_outreach_record(
            influencer_name=influencer_name,
            email="Not Found",
            channel_id=channel_id,
            collaboration_angle=collaboration_angle,
            status="SKIPPED_NO_EMAIL",
            notes="No valid contact email found in profile.",
        )
        return {
            "influencer": influencer_name,
            "status": "SKIPPED_NO_EMAIL",
            "reason": "Missing email",
        }

    # 2. Prevent duplicate outreach
    if is_already_contacted(email, channel_id):
        log_outreach_record(
            influencer_name=influencer_name,
            email=email,
            channel_id=channel_id,
            collaboration_angle=collaboration_angle,
            status="SKIPPED_DUPLICATE",
            notes="Creator was already contacted previously. Deduplication prevented re-send.",
        )
        return {
            "influencer": influencer_name,
            "status": "SKIPPED_DUPLICATE",
            "reason": "Already contacted",
        }

    subject = f"Collaboration with EDXSO – {collaboration_angle}"

    # 3. Deliver via Safe Simulation Mode or Live SMTP
    if simulate:
        log_outreach_record(
            influencer_name=influencer_name,
            email=email,
            channel_id=channel_id,
            collaboration_angle=collaboration_angle,
            status="SIMULATED",
            notes=f"Safe simulation verified. Subject: '{subject}'",
        )
        return {
            "influencer": influencer_name,
            "status": "SIMULATED",
            "email": email,
            "subject": subject,
        }
    else:
        try:
            send_real_email(to_email=email, subject=subject, body=email_pitch)
            log_outreach_record(
                influencer_name=influencer_name,
                email=email,
                channel_id=channel_id,
                collaboration_angle=collaboration_angle,
                status="SENT",
                notes=f"Successfully delivered via SMTP. Subject: '{subject}'",
            )
            return {
                "influencer": influencer_name,
                "status": "SENT",
                "email": email,
            }
        except Exception as err:
            logger.error(f"Failed to deliver email to {email}: {err}")
            log_outreach_record(
                influencer_name=influencer_name,
                email=email,
                channel_id=channel_id,
                collaboration_angle=collaboration_angle,
                status="FAILED",
                notes=f"SMTP delivery error: {str(err)}",
            )
            return {
                "influencer": influencer_name,
                "status": "FAILED",
                "error": str(err),
            }


def prepare_instagram_dm_workflow(
    influencer_name: str, handle: Optional[str], dm_text: str
) -> Dict:
    """Create a simulated / manual workflow for Instagram DMs adhering to API policies."""
    clean_handle = handle.lstrip("@") if handle else influencer_name.lower().replace(" ", "")
    profile_url = f"https://www.instagram.com/{clean_handle}"

    return {
        "influencer": influencer_name,
        "instagram_handle": f"@{clean_handle}",
        "profile_url": profile_url,
        "dm_text": dm_text,
        "status": "MANUAL_WORKFLOW_READY",
        "action_required": "Copy text & dispatch via Instagram web or mobile app",
    }


def dispatch_all_pitches(
    messages_path: Path = MESSAGES_INPUT_PATH,
    filtered_path: Path = FILTERED_DATA_PATH,
    simulate: bool = True,
) -> List[Dict]:
    """Execute batch dispatch for all qualified pitches and update the tracking log."""
    if not messages_path.exists():
        raise FileNotFoundError(f"Messages file not found at {messages_path}")

    with open(messages_path, "r", encoding="utf-8") as f:
        messages = json.load(f)

    # Load filtered data to map channel IDs and emails
    channel_id_map = {}
    email_map = {}
    if filtered_path.exists():
        with open(filtered_path, "r", encoding="utf-8") as f:
            fdata = json.load(f)
            for item in fdata.get("qualified_influencers", []):
                p = item["profile"]
                channel_id_map[p["name"]] = p.get("channel_id", "")
                email_map[p["name"]] = p.get("contact_email", "Not Found")

    results = []
    logger.info(
        f"Starting outreach dispatch for {len(messages)} creators (Simulate={simulate})..."
    )

    for item in messages:
        name = item.get("influencer_name", "")
        email = email_map.get(name, item.get("contact_email", "Not Found"))
        channel_id = channel_id_map.get(name, "")
        angle = item.get("collaboration_angle", "Sponsorship")
        email_pitch = item.get("email_pitch", "")

        res = dispatch_email_pitch(
            influencer_name=name,
            email=email,
            channel_id=channel_id,
            collaboration_angle=angle,
            email_pitch=email_pitch,
            simulate=simulate,
        )
        results.append(res)

    logger.info(f"Dispatch finished. Tracker log updated at {OUTREACH_TRACKER_PATH}")
    return results


if __name__ == "__main__":
    outcomes = dispatch_all_pitches(simulate=True)
    print("\n" + "=" * 55)
    print("OUTREACH DISPATCH SUMMARY (SAFE SIMULATION MODE)")
    print("=" * 55)
    for res in outcomes:
        status = res.get("status")
        name = res.get("influencer")
        print(f" - [{status}] {name}")
    print("=" * 55)

