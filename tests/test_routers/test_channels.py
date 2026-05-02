"""Tests for channels router."""
from __future__ import annotations

from fastapi.testclient import TestClient


API_PREFIX = "/api/v1"


def test_create_channel(client: TestClient) -> None:
    payload = {
        "youtube_id": "UCtestChannel001",
        "title": "Test Channel",
        "description": "A test channel for pytest",
        "subscriber_count": 1000,
        "video_count": 10,
        "view_count": 50000,
        "country": "US",
        "language": "en",
        "niche": "test_niche",
    }
    response = client.post(f"{API_PREFIX}/channels", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["youtube_id"] == payload["youtube_id"]
    assert data["title"] == payload["title"]
    assert data["id"] is not None


def test_create_channel_duplicate(client: TestClient) -> None:
    payload = {
        "youtube_id": "UCtestChannel002",
        "title": "Duplicate Test",
    }
    r1 = client.post(f"{API_PREFIX}/channels", json=payload)
    assert r1.status_code == 201

    r2 = client.post(f"{API_PREFIX}/channels", json=payload)
    assert r2.status_code == 409


def test_list_channels(client: TestClient) -> None:
    response = client.get(f"{API_PREFIX}/channels")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)


def test_get_channel(client: TestClient) -> None:
    # Create a channel first
    payload = {
        "youtube_id": "UCtestChannel003",
        "title": "Get Test Channel",
    }
    create_resp = client.post(f"{API_PREFIX}/channels", json=payload)
    assert create_resp.status_code == 201
    created = create_resp.json()

    response = client.get(f"{API_PREFIX}/channels/{created['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]
    assert data["youtube_id"] == payload["youtube_id"]


def test_get_channel_not_found(client: TestClient) -> None:
    response = client.get(f"{API_PREFIX}/channels/999999")
    assert response.status_code == 404


def test_update_channel(client: TestClient) -> None:
    payload = {
        "youtube_id": "UCtestChannel004",
        "title": "Before Update",
    }
    create_resp = client.post(f"{API_PREFIX}/channels", json=payload)
    assert create_resp.status_code == 201
    created = create_resp.json()

    update_resp = client.put(
        f"{API_PREFIX}/channels/{created['id']}",
        json={"title": "After Update", "niche": "updated_niche"},
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["title"] == "After Update"
    assert data["niche"] == "updated_niche"


def test_delete_channel(client: TestClient) -> None:
    payload = {
        "youtube_id": "UCtestChannel005",
        "title": "Delete Me",
    }
    create_resp = client.post(f"{API_PREFIX}/channels", json=payload)
    assert create_resp.status_code == 201
    created = create_resp.json()

    del_resp = client.delete(f"{API_PREFIX}/channels/{created['id']}")
    assert del_resp.status_code == 204

    get_resp = client.get(f"{API_PREFIX}/channels/{created['id']}")
    assert get_resp.status_code == 404
