"""Outreach tracking manager and duplicate prevention state machine."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

from src.config import OUTREACH_TRACKER_PATH

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

TRACKER_COLUMNS = [
    "Influencer",
    "Email",
    "Message Generated",
    "Sent",
    "Date",
    "Status",
    "Channel ID",
    "Collaboration Angle",
    "Notes",
]


def initialize_tracker(tracker_path: Path = OUTREACH_TRACKER_PATH) -> pd.DataFrame:
    """Initialize or load the outreach tracker CSV."""
    if tracker_path.exists():
        try:
            return pd.read_csv(tracker_path)
        except Exception as err:
            logger.warning(f"Could not read existing tracker, initializing fresh: {err}")

    df = pd.DataFrame(columns=TRACKER_COLUMNS)
    tracker_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(tracker_path, index=False)
    return df


def is_already_contacted(
    email: str, channel_id: str, tracker_path: Path = OUTREACH_TRACKER_PATH
) -> bool:
    """Check if an influencer has already been contacted to prevent duplicate outreach."""
    if not tracker_path.exists():
        return False

    try:
        df = pd.read_csv(tracker_path)
        if df.empty:
            return False

        # Exclude failed attempts, check successful dispatches
        successful_statuses = ["SENT", "SIMULATED"]

        # Check by valid email
        if email and email.lower() != "not found":
            matches = df[
                (df["Email"].str.lower() == email.lower())
                & (df["Status"].isin(successful_statuses))
            ]
            if not matches.empty:
                return True

        # Check by unique channel ID
        if channel_id:
            matches_id = df[
                (df["Channel ID"] == channel_id)
                & (df["Status"].isin(successful_statuses))
            ]
            if not matches_id.empty:
                return True

        return False
    except Exception as err:
        logger.error(f"Error checking duplicate status: {err}")
        return False


def log_outreach_record(
    influencer_name: str,
    email: str,
    channel_id: str,
    collaboration_angle: str,
    status: str,
    notes: str = "",
    tracker_path: Path = OUTREACH_TRACKER_PATH,
) -> Dict:
    """Append a structured delivery record to the outreach log."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sent_flag = "Yes" if status in ["SENT", "SIMULATED"] else "No"
    message_generated = "Yes"

    new_row = {
        "Influencer": influencer_name,
        "Email": email,
        "Message Generated": message_generated,
        "Sent": sent_flag,
        "Date": now_str,
        "Status": status,
        "Channel ID": channel_id,
        "Collaboration Angle": collaboration_angle,
        "Notes": notes,
    }

    df = initialize_tracker(tracker_path)
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(tracker_path, index=False)

    logger.info(f"Logged outreach for {influencer_name} -> Status: {status}")
    return new_row


def get_tracker_stats(tracker_path: Path = OUTREACH_TRACKER_PATH) -> Dict:
    """Return summary statistics of all outreach attempts."""
    df = initialize_tracker(tracker_path)
    if df.empty:
        return {
            "total_records": 0,
            "total_sent": 0,
            "total_simulated": 0,
            "total_skipped_duplicate": 0,
            "total_skipped_no_email": 0,
        }

    return {
        "total_records": len(df),
        "total_sent": int((df["Status"] == "SENT").sum()),
        "total_simulated": int((df["Status"] == "SIMULATED").sum()),
        "total_skipped_duplicate": int((df["Status"] == "SKIPPED_DUPLICATE").sum()),
        "total_skipped_no_email": int((df["Status"] == "SKIPPED_NO_EMAIL").sum()),
    }

