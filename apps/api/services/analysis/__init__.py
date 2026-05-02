"""Analysis algorithms package — modular algorithm implementations.

This package splits the original monolithic analyzer.py into focused modules:
  - common: Shared data models (dataclasses)
  - viral: Short-term viral detection (Algorithm 1)
  - evergreen: Long-tail evergreen detection (Algorithm 2)
  - sentiment: Comment sentiment analysis (Algorithm 3)
  - monetization: Monetization signal detection (Algorithm 4)
  - niche: Niche scoring card (Algorithm 5)
  - format: Video format analyzer + thumbnail CTR estimator (Algorithm 7-8)
  - kpi: Dashboard KPI calculator + scheduler engine (Algorithm 9-10)
"""
from __future__ import annotations

from .common import (
    EvergreenDetectionResult,
    KeywordMetrics,
    MonetizationResult,
    NicheMetrics,
    NicheScoringResult,
    SentimentResult,
    VideoMetrics,
    ViralDetectionResult,
)
from .evergreen import LongTailEvergreenDetector
from .format import ThumbnailCTREstimator, VideoFormatAnalyzer
from .kpi import DashboardKPICalculator, SchedulerEngine
from .monetization import MonetizationSignalDetector
from .niche import NicheScoringCard
from .sentiment import CommentSentimentAnalyzer
from .viral import ShortTermViralDetector

__all__ = [
    # Data models
    "VideoMetrics",
    "ViralDetectionResult",
    "KeywordMetrics",
    "EvergreenDetectionResult",
    "SentimentResult",
    "MonetizationResult",
    "NicheMetrics",
    "NicheScoringResult",
    # Algorithm classes
    "ShortTermViralDetector",
    "LongTailEvergreenDetector",
    "CommentSentimentAnalyzer",
    "MonetizationSignalDetector",
    "NicheScoringCard",
    "VideoFormatAnalyzer",
    "ThumbnailCTREstimator",
    "DashboardKPICalculator",
    "SchedulerEngine",
]
