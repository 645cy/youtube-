"""Tests for radar router monitor lifecycle."""
from __future__ import annotations

from fastapi.testclient import TestClient


API_PREFIX = "/api/v1"


def test_radar_monitor_create_update_list_and_delete(client: TestClient) -> None:
    channel = client.post(
        f"{API_PREFIX}/channels",
        json={"youtube_id": "UCradarTest001", "title": "Radar Test Channel"},
    )
    assert channel.status_code == 201
    channel_id = channel.json()["id"]

    created = client.post(
        f"{API_PREFIX}/radar/monitors",
        json={"channel_id": channel_id, "job_type": "new_videos", "frequency": "daily"},
    )
    assert created.status_code == 201
    job_id = created.json()["id"]

    updated = client.put(f"{API_PREFIX}/radar/monitors/{job_id}", json={"status": "paused"})
    listed = client.get(f"{API_PREFIX}/radar/monitors")
    deleted = client.delete(f"{API_PREFIX}/radar/monitors/{job_id}")
    missing = client.get(f"{API_PREFIX}/radar/monitors/{job_id}")

    assert updated.status_code == 200
    assert updated.json()["status"] == "paused"
    assert any(item["id"] == job_id for item in listed.json())
    assert deleted.status_code == 204
    assert missing.status_code == 404  # CRG: Radar management endpoints need router-level regression coverage.
