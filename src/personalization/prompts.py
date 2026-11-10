"""Prompt templates, professional communication guidelines, and guardrails."""

from typing import Dict, Optional


SYSTEM_INSTRUCTION = """You are a senior brand partnerships lead at EDXSO, an engineering-driven AI platform.
Your objective is to write authentic, executive-level outreach messages to technical creators and educators.

COMMUNICATION PRINCIPLES & GUARDRAILS:
1. PEER-TO-PEER ENGINEERING TONE: Write professionally, engineer-to-engineer. Avoid generic influencer marketing fluff (e.g. avoid 'I stumbled upon your channel', 'game-changing tool', or 'thrilled to connect').
2. GROUNDING MANDATE: Reference only their verified recent video and stated technical themes. Do NOT invent past content or metrics.
3. CONCISE VALUE PROPOSITION: Articulate clearly how EDXSO's AI tools or developer platform provides genuine value to their audience.
4. STRICT WORD LIMITS:
   - Email Pitch: MUST be strictly between 60 and 90 words.
   - Instagram DM: MUST be strictly between 15 and 30 words.
5. LOW-FRICTION CALL TO ACTION: Propose an easy next step (e.g. 'Open to reviewing a brief 1-pager this week?').
6. OUTPUT SCHEMA: Return raw valid JSON with keys: "collaboration_angle", "email_pitch", "instagram_dm".
"""


def select_collaboration_angle(follower_count: int, engagement_rate: float) -> str:
    """Intelligently assign a collaboration angle based on tier and engagement."""
    if follower_count >= 50000:
        return "Sponsorship & Paid Integration"
    elif follower_count >= 20000:
        return "UGC Content Creation & Affiliate Program"
    else:
        return "Brand Ambassador & Early Access Barter"


def build_user_prompt(profile_data: Dict, custom_campaign_notes: Optional[str] = None) -> str:
    """Construct a grounded prompt containing verified creator context and optional campaign notes."""
    name = profile_data.get("name", "Creator")
    followers = profile_data.get("follower_count", 0)
    er = profile_data.get("engagement_rate", 0.0)
    themes = ", ".join(profile_data.get("content_themes", ["Tech & AI"]))
    recent_video = profile_data.get("recent_video_title") or "recent tech tutorials"
    recent_desc = profile_data.get("recent_video_description") or ""
    angle = select_collaboration_angle(followers, er)

    custom_context = (
        f"- Custom Campaign Focus: {custom_campaign_notes}\n"
        if custom_campaign_notes
        else ""
    )

    prompt = f"""Generate outreach messages for this verified influencer:

CREATOR PROFILE (GROUND TRUTH):
- Name: {name}
- Audience: {followers:,} subscribers
- Engagement Rate: {er:.2f}%
- Content Themes: {themes}
- Latest Upload: "{recent_video}"
- Video Context: {recent_desc[:150]}
- Target Angle: {angle}
{custom_context}
SPECIFICATIONS:
1. Email Collaboration Pitch:
   - Target Length: Strictly 60 to 90 words.
   - Tone: Professional, respectful, partnership-oriented.
   - Grounding: Reference "{recent_video}".
   - Proposal: Propose a {angle} around EDXSO developer platform.

2. Instagram DM:
   - Target Length: Strictly 15 to 30 words.
   - Tone: Short, natural, peer-to-peer.

Return ONLY raw JSON in this schema:
{{
  "collaboration_angle": "{angle}",
  "email_pitch": "<email text between 60 and 90 words>",
  "instagram_dm": "<dm text between 15 and 30 words>"
}}
"""
    return prompt
