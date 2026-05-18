"""Tests for crawler router task CRUD."""
from __future__ import annotations

from fastapi.testclient import TestClient


API_PREFIX = "/api/v1"


def test_crawler_task_create_get_list_and_delete(client: TestClient) -> None:
    payload = {
        "name": "Stats smoke task",
        "task_type": "channel_stats",
        "target": "missing-channel",
        "frequency": "manual",
        "config": {},
    }
    created = client.post(f"{API_PREFIX}/crawler/tasks", json=payload)
    assert created.status_code == 201
    task_id = created.json()["id"]

    fetched = client.get(f"{API_PREFIX}/crawler/tasks/{task_id}")
    listed = client.get(f"{API_PREFIX}/crawler/tasks")
    deleted = client.delete(f"{API_PREFIX}/crawler/tasks/{task_id}")
    missing = client.get(f"{API_PREFIX}/crawler/tasks/{task_id}")

    assert fetched.status_code == 200
    assert any(item["id"] == task_id for item in listed.json())
    assert deleted.status_code == 204
    assert missing.status_code == 404  # CRG: Crawler management endpoints need regression coverage.
