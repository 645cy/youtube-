"""Common / Dashboard Pydantic Schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DashboardKPI(BaseModel):
    """看板核心指标."""
    total_channels: int
    total_videos: int
    total_views: int
    total_subscribers: int
    active_monitors: int
    recent_analyses: int
    viral_videos_count: int
    evergreen_videos_count: int
    avg_sentiment_score: float
    top_performing_channel: Optional[str] = None
    monetization_coverage_pct: float
    updated_at: datetime = Field(default_factory=datetime.utcnow)
