"""
Pydantic v2 全量 Schema 定义
覆盖频道、视频、监控任务、分析结果、用户画像、变现路径推荐等全部 DTO.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from apps.api.config import settings


# ── Channel Schemas ──

class ChannelCreate(BaseModel):
    """创建频道请求."""
    youtube_id: str = Field(..., min_length=5, max_length=24)
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    subscriber_count: Optional[int] = Field(None, ge=0)
    video_count: Optional[int] = Field(None, ge=0)
    view_count: Optional[int] = Field(None, ge=0)
    thumbnail_url: Optional[str] = None
    country: Optional[str] = Field(None, max_length=2)
    language: Optional[str] = Field(None, max_length=5)
    niche: Optional[str] = Field(None, max_length=50)


class ChannelRead(BaseModel):
    """频道响应 (含关联视频数)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    youtube_id: str
    title: str
    description: Optional[str] = None
    subscriber_count: Optional[int] = None
    video_count: Optional[int] = None
    view_count: Optional[int] = None
    thumbnail_url: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    niche: Optional[str] = None
    # ── 频道发现字段 ──
    channel_created_at: Optional[datetime] = None
    avg_views_per_video: Optional[int] = None
    discovery_score: Optional[float] = None
    discovery_keyword: Optional[str] = None
    discovered_at: Optional[datetime] = None
    last_stats_updated: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ChannelUpdate(BaseModel):
    """更新频道请求 (全字段可选)."""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    subscriber_count: Optional[int] = None
    video_count: Optional[int] = None
    view_count: Optional[int] = None
    thumbnail_url: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    niche: Optional[str] = None


class ChannelList(BaseModel):
    """频道列表响应."""
    items: list[ChannelRead]
    total: int
    offset: int
    limit: int


# ── Video Schemas ──

class VideoCreate(BaseModel):
    """创建视频记录请求."""
    youtube_id: str = Field(..., min_length=11, max_length=11)
    channel_id: int = Field(..., gt=0)
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    published_at: Optional[datetime] = None
    duration: Optional[int] = Field(None, ge=0)  # 秒
    view_count: Optional[int] = Field(None, ge=0)
    like_count: Optional[int] = Field(None, ge=0)
    comment_count: Optional[int] = Field(None, ge=0)
    thumbnail_url: Optional[str] = None
    tags: Optional[list[str]] = None
    category_id: Optional[str] = None
    language: Optional[str] = None
    is_short: bool = False


class VideoRead(BaseModel):
    """视频响应."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    youtube_id: str
    channel_id: int
    title: str
    description: Optional[str] = None
    published_at: Optional[datetime] = None
    duration: Optional[int] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    thumbnail_url: Optional[str] = None
    tags: Optional[str] = None
    category_id: Optional[str] = None
    language: Optional[str] = None
    is_short: bool
    created_at: datetime


class VideoList(BaseModel):
    """视频列表响应."""
    items: list[VideoRead]
    total: int
    offset: int
    limit: int


class VideoFilter(BaseModel):
    """视频筛选参数."""
    channel_id: Optional[int] = None
    is_short: Optional[bool] = None
    category_id: Optional[str] = None
    language: Optional[str] = None
    min_views: Optional[int] = None
    min_duration: Optional[int] = None
    max_duration: Optional[int] = None
    sort_by: str = "published_at"  # published_at | view_count | created_at
    sort_order: str = "desc"
    offset: int = 0
    limit: int = 50


# ── MonitorJob Schemas ──

class MonitorJobCreate(BaseModel):
    """创建监控任务."""
    channel_id: int = Field(..., gt=0)
    job_type: str = Field(..., pattern="^(stats|new_videos|comments|search)$")
    frequency: str = settings.DEFAULT_MONITOR_FREQUENCY
    config_json: Optional[str] = None  # JSON 字符串


class MonitorJobRead(BaseModel):
    """监控任务响应."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    channel_id: int
    job_type: str
    frequency: str
    status: str
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    config_json: Optional[str] = None
    created_at: datetime


class MonitorWithChannel(BaseModel):
    """监控任务 + 关联频道信息."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    channel_id: int
    channel_name: str = ""
    channel_thumbnail: str = ""
    subscriber_count: int = 0
    job_type: str
    frequency: str
    status: str
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime


class MonitorJobUpdate(BaseModel):
    """更新监控任务."""
    frequency: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|paused|error|archived)$")
    config_json: Optional[str] = None
    next_run_at: Optional[datetime] = None


# Crawler Task Schemas

class CrawlerTaskCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    task_type: str = Field(settings.DEFAULT_CRAWLER_TASK_TYPE, pattern="^(channel_latest|keyword_search|channel_stats|channel_discovery)$")
    target: str = Field(..., min_length=1, max_length=500)
    frequency: str = settings.DEFAULT_CRAWLER_FREQUENCY
    config: Dict[str, Any] = Field(default_factory=dict)


class CrawlerTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    task_type: str
    target: str
    frequency: str
    status: str
    config_json: Optional[str] = None
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    latest_run_status: Optional[str] = None
    latest_run_message: Optional[str] = None
    latest_items_found: int = 0


class CrawlerTaskRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    status: str
    source_status: Optional[str] = None
    message: Optional[str] = None
    items_found: int
    result_json: Optional[str] = None
    started_at: datetime
    finished_at: Optional[datetime] = None


# ── Analysis Schemas ──

class AnalysisRequest(BaseModel):
    """发起分析请求."""
    target_type: str = Field(..., pattern="^(video|channel|niche)$")
    target_id: str  # video_id 或 youtube_id 或 niche 名称
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
    viral_level: str  # none | potential | small | big | super
    vri: float  # Viral Ratio Index
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
    sentiment: str  # positive | negative | neutral
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
    opportunity_level: str  # blue_ocean | viable | saturated | avoid
    swot_summary: dict[str, list[str]]
    recommendation: str


class AnalysisResult(BaseModel):
    """统一分析响应."""
    analysis_type: str
    target_id: str
    target_type: str
    status: str  # success | error | pending
    result: dict[str, Any] = {}
    score: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: Optional[int] = None


# ── MetricHistory Schemas ──

class MetricHistoryCreate(BaseModel):
    """创建指标历史记录."""
    channel_id: Optional[int] = None
    video_id: Optional[int] = None
    metric_type: str = Field(..., pattern="^(subscriber|view|like|comment)$")
    value: float


class MetricHistoryRead(BaseModel):
    """指标历史响应."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    channel_id: Optional[int] = None
    video_id: Optional[int] = None
    metric_type: str
    value: float
    recorded_at: datetime


# ── OCP Lab Schemas (用户画像 + 推荐) ──

class UserSkill(BaseModel):
    """用户技能项."""
    name: str
    level: int = Field(1, ge=1, le=10)  # 1-10


class UserProfile(BaseModel):
    """OCP 实验室用户画像.

    五维画像模型: 技能、时间、资金、兴趣、设备.
    """
    # 技能维度
    skills: list[UserSkill] = []  # 视频剪辑、写作、编程、设计等
    has_camera: bool = False
    has_mic: bool = False
    editing_experience: int = Field(0, ge=0, le=10)

    # 时间维度
    weekly_hours: float = Field(10, ge=0, le=168)  # 每周可用小时
    preferred_video_length: str = "medium"  # short | medium | long
    can_show_face: bool = True

    # 资金维度
    monthly_budget_usd: float = Field(0, ge=0)  # 月预算 (USD)
    willing_to_invest: bool = False

    # 兴趣维度
    interests: list[str] = []  # 科技、教育、娱乐、生活方式等
    native_language: str = "zh"  # 母语
    target_audience: str = settings.DEFAULT_TARGET_REGION  # global | local

    # 设备维度
    has_computer: bool = True
    computer_os: str = "windows"  # windows | mac | linux
    has_smartphone: bool = True


class PathRecommendation(BaseModel):
    """单条变现路径推荐结果."""
    path_id: int
    path_name: str
    path_name_en: str
    match_score: float  # 0-100 匹配分数
    match_reasons: list[str]  # 匹配原因说明
    estimated_startup_cost: float  # 预估启动成本
    estimated_monthly_income_low: float
    estimated_monthly_income_high: float
    time_to_first_income_months: int
    difficulty: str  # beginner | intermediate | advanced
    required_tools: list[str]
    workflow_steps: list[str]
    pros: list[str]
    cons: list[str]


class RecommendationResponse(BaseModel):
    """推荐响应."""
    user_profile_summary: dict[str, Any]
    recommendations: list[PathRecommendation]
    top_path: Optional[PathRecommendation] = None
    personalized_workflow: Optional[dict[str, Any]] = None


# ── Dashboard KPI Schema ──

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
