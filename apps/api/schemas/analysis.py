"""Analysis Pydantic Schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class AnalysisRequest(BaseModel):
    """发起分析请求."""
    target_type: str = Field(..., pattern="^(video|channel|niche)$")
    target_id: str
    analysis_types: list[str] = Field(default=["viral_detection"])

    @field_validator("analysis_types")
    @classmethod
    def validate_analysis_types(cls, v: list[str]) -> list[str]:
        allowed = {"viral_detection", "evergreen", "sentiment", "monetization", "niche_score"}
        for item in v:
            if item not in allowed:
                raise ValueError(f"Invalid analysis_type: {item}. Allowed: {allowed}")
        return v


class ViralDetectionResult(BaseModel):
    """爆款检测结果."""
    is_viral: bool
    viral_score: float
    viral_level: str
    vri: float
    velocity_index: float
    estimated_peak_views: int
    confidence: float
    recommendation: str


class EvergreenResult(BaseModel):
    """长尾 Evergreen 检测结果."""
    is_evergreen: bool
    evergreen_score: float
    search_stability_index: float
    competition_ratio: float
    traffic_type: str
    estimated_monthly_views: int
    recommendation: str


class SentimentResult(BaseModel):
    """评论情感分析结果."""
    comment_id: str
    text: str
    compound_score: float
    positive_score: float
    negative_score: float
    neutral_score: float
    sentiment: str
    key_positive_words: list[str]
    key_negative_words: list[str]


class SentimentAggregation(BaseModel):
    """频道级情感聚合."""
    total_comments: int
    positive_pct: float
    negative_pct: float
    neutral_pct: float
    avg_compound: float
    health_score: float
    top_positive_words: list[str]
    top_negative_words: list[str]


class MonetizationResult(BaseModel):
    """变现信号检测结果."""
    video_id: str
    is_monetized: bool
    monetization_score: float
    affiliate_detected: bool
    affiliate_confidence: float
    sponsorship_detected: bool
    sponsorship_score: float
    detected_coupons: list[str]
    monetization_types: list[str]
    disclosure_compliance: str
    estimated_monthly_revenue_tier: str


class NicheScoreResult(BaseModel):
    """Niche 打分卡结果."""
    niche_name: str
    total_score: float
    traffic_potential: float
    monetization_density: float
    ai_replaceability: float
    reproducibility: float
    opportunity_level: str
    swot_summary: dict[str, list[str]]
    recommendation: str


class AnalysisResult(BaseModel):
    """统一分析响应."""
    analysis_type: str
    target_id: str
    target_type: str
    status: str
    result: dict[str, Any] = {}
    score: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: Optional[int] = None
