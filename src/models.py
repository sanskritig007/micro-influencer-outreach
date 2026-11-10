"""Data schemas for influencer discovery, filtering, and outreach tracking."""

from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


class InfluencerProfile(BaseModel):
    """Raw and enriched profile of a discovered influencer."""

    channel_id: str = Field(description="Unique channel/platform ID")
    name: str = Field(description="Influencer / Channel name")
    platform: str = Field(default="YouTube", description="Social media platform")
    profile_url: str = Field(description="Public URL to the influencer's profile")
    follower_count: int = Field(ge=0, description="Follower / Subscriber count")
    engagement_rate: float = Field(ge=0.0, description="Calculated engagement rate percentage")
    niche: str = Field(description="Category or niche")
    content_themes: List[str] = Field(default_factory=list, description="Core themes identified in content")
    
    # Contact & Secondary channels
    contact_email: str = Field(default="Not Found", description="Contact email or strictly 'Not Found'")
    secondary_handles: Optional[str] = Field(default=None, description="Linked Instagram/Twitter/TikTok handle")
    website: Optional[str] = Field(default=None, description="Personal or business website URL")
    
    # Demographics (optional/estimated)
    audience_geography: Optional[str] = Field(default="Global", description="Primary audience geography")
    audience_age: Optional[str] = Field(default="18-34", description="Estimated audience age bracket")
    audience_gender: Optional[str] = Field(default="Mixed", description="Estimated audience gender split")
    
    # Context for AI Personalization
    recent_video_title: Optional[str] = Field(default=None, description="Title of the most recent video/post")
    recent_video_description: Optional[str] = Field(default=None, description="Description/snippet of recent post")

    @field_validator("contact_email")
    @classmethod
    def validate_contact_email(cls, v: str) -> str:
        # Normalize email or explicitly mark as Not Found if missing
        if not v or not v.strip() or "@" not in v:
            return "Not Found"
        return v.strip().lower()


class FilterResult(BaseModel):
    """Audit record of whether an influencer passed or failed criteria and why."""

    influencer_name: str
    channel_id: str
    status: Literal["PASSED", "FAILED"]
    passed: bool
    reasons: List[str] = Field(default_factory=list, description="Detailed explanation of pass or fail")
    follower_count: int
    engagement_rate: float
    niche_relevance_score: float = Field(ge=0.0, le=1.0, default=1.0)


class OutreachPitch(BaseModel):
    """Generated personalized outreach messages."""

    influencer_name: str
    contact_email: str
    collaboration_angle: str = Field(
        description="Collaboration type: Sponsorship, UGC, Affiliate, Brand Ambassador, Barter"
    )
    email_pitch: str = Field(
        description="Personalized email pitch (target: 60-90 words)"
    )
    email_word_count: int
    instagram_dm: str = Field(
        description="Personalized short DM (target: 15-30 words)"
    )
    dm_word_count: int
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class OutreachTrackerRecord(BaseModel):
    """Outreach delivery record for the tracking log."""

    influencer_name: str
    email: str
    channel_id: str
    collaboration_angle: str
    email_pitch: str
    instagram_dm: str
    status: Literal["PENDING", "SENT", "SIMULATED", "SKIPPED_NO_EMAIL", "SKIPPED_DUPLICATE", "FAILED"]
    sent_date: Optional[str] = None
    notes: Optional[str] = None

