"""Pydantic v2 Schema Package.

All schemas are re-exported here for backward compatibility.
Example:
    from apps.api.schemas import ChannelCreate, VideoRead
"""
from __future__ import annotations

# Channel
from .channel import ChannelCreate, ChannelList, ChannelRead, ChannelUpdate

# Video
from .video import VideoCreate, VideoFilter, VideoList, VideoRead

# Monitor
from .monitor import (
    MonitorJobCreate,
    MonitorJobRead,
    MonitorJobUpdate,
    MonitorWithChannel,
)

# Crawler
from .crawler import CrawlerTaskCreate, CrawlerTaskRead, CrawlerTaskRunRead

# Analysis
from .analysis import (
    AnalysisRequest,
    AnalysisResult,
    EvergreenResult,
    MonetizationResult,
    NicheScoreResult,
    SentimentAggregation,
    SentimentResult,
    ViralDetectionResult,
)

# Metric
from .metric import MetricHistoryCreate, MetricHistoryRead

# Lab
from .lab import (
    PathRecommendation,
    RecommendationResponse,
    UserProfile,
    UserSkill,
)

# Common / Dashboard
from .common import DashboardKPI

__all__ = [
    # Channel
    "ChannelCreate",
    "ChannelRead",
    "ChannelUpdate",
    "ChannelList",
    # Video
    "VideoCreate",
    "VideoRead",
    "VideoList",
    "VideoFilter",
    # Monitor
    "MonitorJobCreate",
    "MonitorJobRead",
    "MonitorJobUpdate",
    "MonitorWithChannel",
    # Crawler
    "CrawlerTaskCreate",
    "CrawlerTaskRead",
    "CrawlerTaskRunRead",
    # Analysis
    "AnalysisRequest",
    "AnalysisResult",
    "ViralDetectionResult",
    "EvergreenResult",
    "SentimentResult",
    "SentimentAggregation",
    "MonetizationResult",
    "NicheScoreResult",
    # Metric
    "MetricHistoryCreate",
    "MetricHistoryRead",
    # Lab
    "UserSkill",
    "UserProfile",
    "PathRecommendation",
    "RecommendationResponse",
    # Common
    "DashboardKPI",
]
