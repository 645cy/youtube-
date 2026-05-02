"""爆款检测算法 + 变现信号识别引擎

**DEPRECATED**: This monolithic module has been split into the
`apps.api.services.analysis` package for better maintainability.

Please import from the new package:
  from apps.api.services.analysis import ShortTermViralDetector
  from apps.api.services.analysis.viral import ShortTermViralDetector

This file is kept as a backward-compatible barrel re-export.
"""
from __future__ import annotations

# Re-export everything from the new modular package to maintain compatibility
# with existing imports across routers, services, and tests.
from apps.api.services.analysis import (  # noqa: F401
    CommentSentimentAnalyzer,
    DashboardKPICalculator,
    EvergreenDetectionResult,
    KeywordMetrics,
    LongTailEvergreenDetector,
    MonetizationResult,
    MonetizationSignalDetector,
    NicheMetrics,
    NicheScoringCard,
    NicheScoringResult,
    SchedulerEngine,
    SentimentResult,
    ShortTermViralDetector,
    ThumbnailCTREstimator,
    VideoFormatAnalyzer,
    VideoMetrics,
    ViralDetectionResult,
)
