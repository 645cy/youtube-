"""Tests for YouTube API service layer (quota, metadata, offline logic)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from apps.api.services.youtube_api import (
    EndpointCost,
    QuotaManager,
    QuotaSnapshot,
    VideoMetadata,
)


class TestQuotaSnapshot:
    """Tests for QuotaSnapshot state machine."""

    def test_initial_state(self) -> None:
        snap = QuotaSnapshot()
        assert snap.is_exhausted() is False
        assert snap.units_remaining == 10000

    def test_exhausted(self) -> None:
        snap = QuotaSnapshot(units_consumed=9950, units_remaining=50)
        assert snap.is_exhausted(buffer=100) is True
        assert snap.is_exhausted(buffer=30) is False

    def test_with_call(self) -> None:
        snap = QuotaSnapshot(units_consumed=100, units_remaining=9900)
        new = snap.with_call("videos", 1)
        assert new.units_consumed == 101
        assert new.units_remaining == 9899
        assert len(new.call_log) == 1

    def test_reset_if_needed(self) -> None:
        today = datetime.now(timezone.utc)
        # Same day — no reset
        snap = QuotaSnapshot(
            units_consumed=5000, units_remaining=5000, last_reset_utc=today
        )
        reset = snap.reset_if_needed()
        assert reset.units_consumed == 5000

        # Different day — reset
        yesterday = today - timedelta(days=1)
        snap2 = QuotaSnapshot(
            units_consumed=9000, units_remaining=1000, last_reset_utc=yesterday
        )
        reset2 = snap2.reset_if_needed()
        assert reset2.units_consumed == 0
        assert reset2.units_remaining == 10000
        assert reset2.call_log == []


class TestQuotaManager:
    """Tests for QuotaManager budget tracking."""

    @pytest.mark.anyio
    async def test_check_budget_initial(self) -> None:
        manager = QuotaManager(daily_quota=1000)
        # 1000 remaining, buffer=1 -> 1000 > 1 = True
        assert await manager.check_budget(needed=1) is True
        # 1000 remaining, buffer=999 -> 1000 > 999 = True
        assert await manager.check_budget(needed=999) is True
        # 1000 remaining, buffer=1000 -> 1000 > 1000 = False
        assert await manager.check_budget(needed=1000) is False

    @pytest.mark.anyio
    async def test_record_and_budget(self) -> None:
        manager = QuotaManager(daily_quota=1000)
        await manager.record(EndpointCost.VIDEOS_LIST)
        report = await manager.get_usage_report()
        assert report["units_consumed"] == 1
        assert report["units_remaining"] == 999
        assert report["calls_total"] == 1
        assert "VIDEOS_LIST" in report["endpoints"]

    @pytest.mark.anyio
    async def test_multiple_records(self) -> None:
        manager = QuotaManager(daily_quota=1000)
        # EndpointCost enum: equal values share the same instance
        # CHANNELS_LIST.value == 1, same as VIDEOS_LIST, so name becomes VIDEOS_LIST
        await manager.record(EndpointCost.SEARCH_LIST)
        await manager.record(EndpointCost.VIDEOS_LIST)
        report = await manager.get_usage_report()
        assert report["units_consumed"] == 101  # 100 + 1
        assert report["endpoints"]["SEARCH_LIST"] == 100
        assert report["endpoints"]["VIDEOS_LIST"] == 1

    @pytest.mark.anyio
    async def test_record_with_custom_cost(self) -> None:
        manager = QuotaManager(daily_quota=1000)
        # Custom cost works only with string endpoint
        await manager.record("custom_endpoint", cost=10)
        await manager.record("custom_endpoint", cost=5)
        report = await manager.get_usage_report()
        assert report["units_consumed"] == 15
        assert report["endpoints"]["custom_endpoint"] == 15


class TestVideoMetadata:
    """Tests for VideoMetadata dataclass."""

    def test_creation(self) -> None:
        vm = VideoMetadata(
            video_id="dQw4w9WgXcQ",
            title="Never Gonna Give You Up",
            description="Official music video",
            channel_id="UCuAXwgsIb",
            channel_title="Rick Astley",
            upload_date="20091025",
            duration_seconds=212,
            view_count=1500000000,
            like_count=10000000,
            comment_count=500000,
            tags=["pop", "80s"],
            categories=["Music"],
            thumbnail_url="https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
            language="en",
            is_live=False,
            availability="public",
        )
        assert vm.video_id == "dQw4w9WgXcQ"
        assert vm.duration_seconds == 212
        assert vm.view_count == 1500000000
        assert vm.is_live is False
