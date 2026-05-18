"""Tests for apps.api.services.video_service pure functions."""
from __future__ import annotations

import pytest
from sqlalchemy import select

from apps.api.services.video_service import (
    ALLOWED_VIDEO_SORT_FIELDS,
    apply_video_sorting,
    build_video_filters,
    build_video_from_youtube_item,
    parse_iso8601_duration,
    safe_int_stat,
)
from packages.db.schema import Video


class TestParseIso8601Duration:
    def test_parses_full_duration(self) -> None:
        assert parse_iso8601_duration("PT1H2M3S") == 3723

    def test_parses_minutes_only(self) -> None:
        assert parse_iso8601_duration("PT5M30S") == 330

    def test_parses_seconds_only(self) -> None:
        assert parse_iso8601_duration("PT45S") == 45

    def test_returns_none_for_empty(self) -> None:
        assert parse_iso8601_duration(None) is None
        assert parse_iso8601_duration("") is None

    def test_returns_none_for_invalid(self) -> None:
        assert parse_iso8601_duration("not-a-duration") is None


class TestSafeIntStat:
    def test_extracts_int_from_string(self) -> None:
        assert safe_int_stat({"viewCount": "12345"}, "viewCount") == 12345

    def test_returns_none_when_missing(self) -> None:
        assert safe_int_stat({}, "viewCount") is None
        assert safe_int_stat({"viewCount": None}, "viewCount") is None


class TestBuildVideoFromYoutubeItem:
    def test_builds_complete_video(self) -> None:
        item = {
            "id": "vid123",
            "snippet": {
                "title": "Test Video",
                "description": "A test",
                "thumbnails": {"high": {"url": "https://thumb.jpg"}},
                "tags": ["python", "ai"],
                "categoryId": "27",
            },
            "statistics": {"viewCount": "1000", "likeCount": "50", "commentCount": "10"},
            "contentDetails": {"duration": "PT5M30S"},
        }
        video = build_video_from_youtube_item(item, channel_id=1)
        assert video is not None
        assert video.youtube_id == "vid123"
        assert video.channel_id == 1
        assert video.title == "Test Video"
        assert video.duration == 330
        assert video.view_count == 1000
        assert video.is_short is False  # 330s > 60s

    def test_identifies_short(self) -> None:
        item = {
            "id": "short1",
            "snippet": {"title": "Short"},
            "contentDetails": {"duration": "PT30S"},
        }
        video = build_video_from_youtube_item(item, channel_id=2)
        assert video is not None
        assert video.is_short is True

    def test_returns_none_when_missing_id(self) -> None:
        assert build_video_from_youtube_item({}, channel_id=1) is None


class TestBuildVideoFilters:
    def test_builds_empty_when_no_params(self) -> None:
        assert build_video_filters(None, None, None, None, None, None, None) == []

    def test_builds_channel_filter(self) -> None:
        conditions = build_video_filters(5, None, None, None, None, None, None)
        assert len(conditions) == 1

    def test_builds_multiple_filters(self) -> None:
        conditions = build_video_filters(1, True, "27", "en", 100, 60, 300)
        assert len(conditions) == 7


class TestApplyVideoSorting:
    def test_allows_valid_fields(self) -> None:
        for field in ALLOWED_VIDEO_SORT_FIELDS:
            query = select(Video)
            result = apply_video_sorting(query, field, "desc")
            assert result is not None

    def test_rejects_invalid_field(self) -> None:
        query = select(Video)
        with pytest.raises(ValueError, match="Invalid sort_by field"):
            apply_video_sorting(query, "invalid_field", "desc")
