"""Focused tests for split analysis modules: format, monetization, kpi, niche, common."""
from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace

from apps.api.services.analysis.common import NicheMetrics
from apps.api.services.analysis.format import ThumbnailCTREstimator, VideoFormatAnalyzer
from apps.api.services.analysis.kpi import DashboardKPICalculator, SchedulerEngine
from apps.api.services.analysis.monetization import MonetizationSignalDetector
from apps.api.services.analysis.niche import NicheScoringCard
from apps.api.services.scheduler import (
    _upload_item_from_ytdlp_meta,
    _uploads_playlist_id,
    _video_payload_from_upload_item,
)


def test_format_and_thumbnail_estimators_return_actionable_scores() -> None:
    viral = VideoFormatAnalyzer.calculate_viral_coefficient(12000, 1000, is_short=True)
    ctr = ThumbnailCTREstimator.estimate("7 ultimate AI tools you must try", has_face=True)
    assert viral["is_viral"] is True
    assert ctr["estimated_ctr_pct"] > 2.0  # CRG: Format and thumbnail modules should expose usable scores.


def test_monetization_detector_finds_affiliate_sponsor_and_coupon() -> None:
    detector = MonetizationSignalDetector()
    result = detector.detect(
        "vid1",
        "Sponsored AI tool review",
        "This video is sponsored by Acme. Buy at https://amzn.to/demo?tag=creator and use code SAVE20.",
    )
    assert result.affiliate_detected is True
    assert result.sponsorship_detected is True
    assert "SAVE20" in result.detected_coupons  # CRG: Monetization tests lock real signal extraction.


def test_kpi_and_scheduler_modules_produce_stable_outputs() -> None:
    kpi = DashboardKPICalculator.calculate(
        channels=[{"title": "A", "subscriber_count": 10, "view_count": 100, "has_active_monitor": True}],
        videos=[{"view_count": 100}, {"view_count": 200}],
        recent_analyses=[{"analysis_type": "monetization", "score": 50}],
    )
    next_run = SchedulerEngine.calculate_next_run(datetime.now() - timedelta(hours=1), 60, 7)
    assert kpi["total_videos"] == 2
    assert next_run >= datetime.now()  # CRG: Scheduler should never recommend a past run.


def test_scheduler_upload_helpers_normalize_video_items() -> None:
    meta = SimpleNamespace(video_id="vid1", title="New upload", thumbnail_url="https://img.example/thumb.jpg")
    item = _upload_item_from_ytdlp_meta(meta)
    payload = _video_payload_from_upload_item(item)
    assert _uploads_playlist_id("UCabc") == "UUabc"
    assert _uploads_playlist_id("@handle") is None
    assert payload == {
        "youtube_id": "vid1",
        "title": "New upload",
        "thumbnail_url": "https://img.example/thumb.jpg",
    }  # CRG: Scheduler API and yt-dlp paths should feed one normalized insert payload.


def test_niche_scoring_module_returns_opportunity_payload() -> None:
    metrics = NicheMetrics(
        niche_name="ai_tools",
        monthly_search_volume=100000,
        growth_trend_12m=0.2,
        avg_rpm=5.0,
        max_rpm_in_niche=10.0,
        competing_channels_count=80,
        avg_video_upload_frequency=2.0,
        evergreen_content_ratio=0.7,
        ai_content_detected_ratio=0.2,
        personality_dependency=0.6,
        required_skill_level=5,
        creator_skill_level=7,
        weekly_time_available=15,
        estimated_production_hours=5,
        passion_score=8,
        startup_cost_estimate=100,
    )
    result = NicheScoringCard().score(metrics)
    assert result.niche_name == "ai_tools"
    assert result.total_score > 0  # CRG: Niche module should produce a non-empty scorecard.
