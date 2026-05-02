"""Shared data models for analysis algorithms."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class VideoMetrics:
    """视频早期指标数据类 (Algorithm 1 输入)."""
    video_id: str
    channel_subscribers: int
    publish_time: datetime
    views_history: list[tuple[datetime, int]]
    ctr_history: list[tuple[datetime, float]]
    retention_history: list[tuple[datetime, float]]
    video_type: str  # shorts | long_form


@dataclass
class ViralDetectionResult:
    """爆款检测结果."""
    is_viral: bool
    viral_score: float
    viral_level: str  # none | potential | small | big | super
    vri: float
    velocity_index: float
    estimated_peak_views: int
    confidence: float
    recommendation: str


@dataclass
class KeywordMetrics:
    """关键词/主题指标 (Algorithm 2 输入)."""
    keyword: str
    monthly_search_volume: int
    weekly_search_history: list[float]
    competing_videos_count: int
    top_video_age_days: int
    avg_view_count_top10: int
    niche: str


@dataclass
class EvergreenDetectionResult:
    """长尾 Evergreen 识别结果."""
    is_evergreen: bool
    evergreen_score: float
    search_stability_index: float
    competition_ratio: float
    traffic_type: str
    estimated_monthly_views: int
    recommendation: str


@dataclass
class SentimentResult:
    """单条评论情感分析结果."""
    comment_id: str
    text: str
    compound_score: float
    positive_score: float
    negative_score: float
    neutral_score: float
    sentiment: str
    key_positive_words: list[str]
    key_negative_words: list[str]


@dataclass
class MonetizationResult:
    """变现信号识别结果."""
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


@dataclass
class NicheMetrics:
    """Niche 评估输入指标."""
    niche_name: str
    monthly_search_volume: int
    growth_trend_12m: float
    avg_rpm: float
    max_rpm_in_niche: float
    competing_channels_count: int
    avg_video_upload_frequency: float
    evergreen_content_ratio: float
    ai_content_detected_ratio: float
    personality_dependency: float
    required_skill_level: float
    creator_skill_level: float
    weekly_time_available: float
    estimated_production_hours: float
    passion_score: float
    startup_cost_estimate: float


@dataclass
class NicheScoringResult:
    """Niche 评分结果."""
    niche_name: str
    total_score: float
    traffic_potential: float
    monetization_density: float
    ai_replaceability: float
    reproducibility: float
    opportunity_level: str
    swot_summary: dict[str, list[str]]
    recommendation: str
