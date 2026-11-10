"""Influencer filtering, qualification, and audit trail classification."""

import json
import logging
from typing import Dict, List, Tuple
from pathlib import Path

from src.config import (
    RAW_DATA_PATH,
    FILTERED_DATA_PATH,
    MIN_FOLLOWERS,
    MAX_FOLLOWERS,
    MIN_ENGAGEMENT_RATE,
    TARGET_NICHE,
)
from src.models import InfluencerProfile, FilterResult

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def evaluate_influencer(
    profile: InfluencerProfile,
    min_followers: int = MIN_FOLLOWERS,
    max_followers: int = MAX_FOLLOWERS,
    min_engagement: float = 0.05,
) -> FilterResult:
    """Evaluate an influencer against predefined criteria and generate an audit result."""
    reasons: List[str] = []
    passed = True

    # 1. Follower count range evaluation (5k - 100k)
    followers = profile.follower_count
    if followers < min_followers:
        passed = False
        reasons.append(
            f"Followers ({followers:,}) below micro-influencer minimum threshold ({min_followers:,})."
        )
    elif followers > max_followers:
        passed = False
        reasons.append(
            f"Followers ({followers:,}) exceed micro-influencer ceiling ({max_followers:,} - Macro tier)."
        )

    # 2. Engagement rate evaluation
    er = profile.engagement_rate
    if er < min_engagement:
        passed = False
        reasons.append(
            f"Engagement rate ({er:.2f}%) below active threshold ({min_engagement:.2f}%)."
        )

    # 3. Niche & content relevance evaluation
    tech_signals = ["ai", "python", "code", "tech", "automation", "developer", "learning", "data"]
    themes_str = " ".join(profile.content_themes).lower()
    name_str = profile.name.lower()
    combined_context = f"{name_str} {themes_str}"

    matches = sum(1 for signal in tech_signals if signal in combined_context)
    relevance_score = min(1.0, round(matches / 3.0, 2))

    if relevance_score < 0.3:
        passed = False
        reasons.append("Content themes show weak alignment with Tech & AI niche.")

    # Final verdict
    if passed:
        reasons.append(
            f"Qualified micro-influencer: {followers:,} followers, {er:.2f}% ER, strong niche alignment."
        )

    status = "PASSED" if passed else "FAILED"

    return FilterResult(
        influencer_name=profile.name,
        channel_id=profile.channel_id,
        status=status,
        passed=passed,
        reasons=reasons,
        follower_count=followers,
        engagement_rate=er,
        niche_relevance_score=relevance_score,
    )


def classify_influencers(
    raw_profiles: List[InfluencerProfile],
) -> Tuple[List[Dict], List[Dict]]:
    """Classify profiles into passed (qualified) and failed (rejected) lists with audit trails."""
    qualified = []
    rejected = []

    for profile in raw_profiles:
        audit = evaluate_influencer(profile)
        record = {
            "profile": profile.model_dump(),
            "audit": audit.model_dump(),
        }

        if audit.passed:
            qualified.append(record)
        else:
            rejected.append(record)

    return qualified, rejected


def run_filtering_pipeline(
    input_path: Path = RAW_DATA_PATH, output_path: Path = FILTERED_DATA_PATH
) -> Dict:
    """Read raw profiles, evaluate and classify them, and save the structured dataset."""
    if not input_path.exists():
        raise FileNotFoundError(f"Raw data file not found at {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    profiles = [InfluencerProfile(**item) for item in raw_data]
    logger.info(f"Loaded {len(profiles)} raw profiles for qualification.")

    qualified, rejected = classify_influencers(profiles)

    output_payload = {
        "niche": TARGET_NICHE,
        "total_evaluated": len(profiles),
        "total_passed": len(qualified),
        "total_failed": len(rejected),
        "pass_rate_pct": round((len(qualified) / max(len(profiles), 1)) * 100, 1),
        "qualified_influencers": qualified,
        "rejected_influencers": rejected,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)

    # Export structured CSV format as requested by assignment deliverable B
    csv_path = output_path.parent / "influencer_dataset.csv"
    rows = []
    for item in qualified:
        p = item["profile"]
        rows.append({
            "Name": p["name"],
            "Platform": p["platform"],
            "Followers": p["follower_count"],
            "Engagement Rate": f"{p['engagement_rate']}%",
            "Niche": p["niche"],
            "Email": p["contact_email"],
            "Profile URL": p["profile_url"],
            "Content Themes": ", ".join(p.get("content_themes", [])),
            "Status": "PASSED",
            "Audit Reason": item["audit"]["reasons"][0],
        })
    for item in rejected:
        p = item["profile"]
        rows.append({
            "Name": p["name"],
            "Platform": p["platform"],
            "Followers": p["follower_count"],
            "Engagement Rate": f"{p['engagement_rate']}%",
            "Niche": p["niche"],
            "Email": p["contact_email"],
            "Profile URL": p["profile_url"],
            "Content Themes": ", ".join(p.get("content_themes", [])),
            "Status": "FAILED",
            "Audit Reason": item["audit"]["reasons"][0],
        })

    import pandas as pd
    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False)

    logger.info(
        f"Filtering complete: {len(qualified)} passed, {len(rejected)} failed. "
        f"Saved JSON to {output_path} and CSV to {csv_path}"
    )

    return output_payload


if __name__ == "__main__":
    result = run_filtering_pipeline()
    print("\n" + "=" * 50)
    print("FILTERING & CLASSIFICATION SUMMARY")
    print("=" * 50)
    print(f"Total Profiles Evaluated : {result['total_evaluated']}")
    print(f"Passed (Qualified)       : {result['total_passed']}")
    print(f"Failed (Rejected)        : {result['total_failed']}")
    print(f"Pass Rate                : {result['pass_rate_pct']}%")
    print("=" * 50)

    print("\nSample Passed Influencers:")
    for item in result["qualified_influencers"][:3]:
        p = item["profile"]
        a = item["audit"]
        print(f" - [PASS] {p['name']} ({p['follower_count']:,} subs, ER: {p['engagement_rate']}%)")
        print(f"   Reason: {a['reasons'][0]}")

    print("\nSample Failed Influencers (with audit reasons):")
    for item in result["rejected_influencers"][:3]:
        p = item["profile"]
        a = item["audit"]
        print(f" - [FAIL] {p['name']} ({p['follower_count']:,} subs, ER: {p['engagement_rate']}%)")
        print(f"   Reason: {a['reasons'][0]}")

