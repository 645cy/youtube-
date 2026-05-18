"""Tests for apps.api.services.channel_service pure functions."""
from __future__ import annotations

import pytest

from apps.api.services.channel_service import (
    build_channel_values,
    missing_thumbnail,
    pick_thumbnail,
    stat_int,
)


class TestPickThumbnail:
    def test_returns_high_quality_first(self) -> None:
        snippet = {"thumbnails": {"high": {"url": " https://high.jpg "}, "medium": {"url": "med.jpg"}}}
        assert pick_thumbnail(snippet) == "https://high.jpg"

    def test_falls_back_to_medium(self) -> None:
        snippet = {"thumbnails": {"medium": {"url": "med.jpg"}, "default": {"url": "def.jpg"}}}
        assert pick_thumbnail(snippet) == "med.jpg"

    def test_falls_back_to_default(self) -> None:
        snippet = {"thumbnails": {"default": {"url": "def.jpg"}}}
        assert pick_thumbnail(snippet) == "def.jpg"

    def test_returns_none_when_empty(self) -> None:
        assert pick_thumbnail({}) is None
        assert pick_thumbnail(None) is None
        assert pick_thumbnail({"thumbnails": {}}) is None


class TestMissingThumbnail:
    def test_detects_missing(self) -> None:
        assert missing_thumbnail(None) is True
        assert missing_thumbnail("") is True
        assert missing_thumbnail("   ") is True

    def test_detects_present(self) -> None:
        assert missing_thumbnail("https://img.jpg") is False


class TestStatInt:
    def test_extracts_integer(self) -> None:
        assert stat_int({"viewCount": "12345"}, "viewCount") == 12345
        assert stat_int({"viewCount": 678}, "viewCount") == 678

    def test_returns_none_when_missing(self) -> None:
        assert stat_int({}, "viewCount") is None
        assert stat_int({"viewCount": None}, "viewCount") is None
        assert stat_int({"viewCount": ""}, "viewCount") is None


class TestBuildChannelValues:
    def test_builds_from_detail_item(self) -> None:
        detail = {
            "snippet": {"title": "Tech Channel", "description": "AI stuff", "country": "US"},
            "statistics": {"subscriberCount": "1000", "videoCount": "50", "viewCount": "9999"},
        }
        result = build_channel_values("UC123", {}, detail)
        assert result["youtube_id"] == "UC123"
        assert result["title"] == "Tech Channel"
        assert result["description"] == "AI stuff"
        assert result["subscriber_count"] == 1000
        assert result["video_count"] == 50
        assert result["view_count"] == 9999
        assert result["country"] == "US"

    def test_falls_back_to_fallback_snippet(self) -> None:
        fallback = {"title": "Fallback Title", "description": "fallback desc"}
        result = build_channel_values("UC456", fallback, None)
        assert result["title"] == "Fallback Title"
        assert result["description"] == "fallback desc"
        assert result["subscriber_count"] is None
        assert result["thumbnail_url"] is None

    def test_uses_detail_over_fallback(self) -> None:
        fallback = {"title": "Fallback", "description": "old"}
        detail = {"snippet": {"title": "Real", "description": "new"}, "statistics": {}}
        result = build_channel_values("UC789", fallback, detail)
        assert result["title"] == "Real"
        assert result["description"] == "new"
