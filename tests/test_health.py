"""Integration tests for health check endpoints."""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_root_redirect(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "YouTube Monitor API"
    assert "docs" in data


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"


def test_health_check_v1(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_youtube_diagnostics(client: TestClient) -> None:
    response = client.get("/api/v1/integrations/youtube/diagnostics")
    assert response.status_code == 200
    data = response.json()
    assert "configured" in data
    assert "key_length" in data
    assert "extractor_ready" in data
