"""Tests for videos router list and import helpers."""
from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.services.video_service import parse_iso8601_duration, build_video_from_youtube_item


API_PREFIX = "/api/v1"


def test_video_list_filter_and_sort(client: TestClient) -> None:
    channel = client.post(f"{API_PREFIX}/channels", json={"youtube_id": "UCvideoList001", "title": "Videos"})
    assert channel.status_code == 201
    channel_id = channel.json()["id"]

    created = client.post(
        f"{API_PREFIX}/videos",
        json={"youtube_id": "vidList0001", "channel_id": channel_id, "title": "Short", "duration": 30},
    )
    response = client.get(f"{API_PREFIX}/videos?channel_id={channel_id}&sort_by=duration&sort_order=asc")

    assert created.status_code == 201
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(item["youtube_id"] == "vidList0001" for item in data["items"])


def test_video_import_helpers_parse_youtube_item() -> None:
    item = {
        "id": "vidImport001",
        "snippet": {
            "title": "Imported",
            "description": "Demo",
            "thumbnails": {"high": {"url": "https://img.example/1.jpg"}},
            "tags": ["ai", "tools"],
            "categoryId": "28",
        },
        "statistics": {"viewCount": "100", "likeCount": "10", "commentCount": "2"},
        "contentDetails": {"duration": "PT1M01S"},
    }
    video = build_video_from_youtube_item(item, channel_id=1)
    assert parse_iso8601_duration("PT1H02M03S") == 3723
    assert video is not None
    assert video.duration == 61
    assert video.is_short is False  # CRG: Import helper should classify videos from parsed duration.
