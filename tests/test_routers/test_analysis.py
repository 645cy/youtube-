"""Tests for analysis router data-contract behavior."""
from __future__ import annotations

from fastapi.testclient import TestClient


API_PREFIX = "/api/v1"


def test_sentiment_skips_when_comments_unavailable(client: TestClient) -> None:
    payload = {
        "target_type": "video",
        "target_id": "missing12345",
        "analysis_types": ["sentiment"],
    }
    response = client.post(f"{API_PREFIX}/analysis/sentiment", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "skipped"
    assert data["score"] is None
    assert data["result"]["source"] == "none"  # CRG: Missing comments must not be hidden by fake analysis.


def test_sentiment_accepts_comments_from_request_schema(client: TestClient) -> None:
    payload = {
        "target_type": "video",
        "target_id": "vidWithComments",
        "analysis_types": ["sentiment"],
        "comments": [["c1", "This is amazing and helpful"], ["c2", "Clear tutorial"]],
    }
    response = client.post(f"{API_PREFIX}/analysis/sentiment", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["result"]["aggregation"]["total_comments"] == 2  # CRG: Comments are part of the real API contract.
    assert data["score"] is not None


def test_growth_marks_estimated_points(client: TestClient) -> None:
    response = client.get(f"{API_PREFIX}/analysis/growth?days=3")
    assert response.status_code == 200
    data = response.json()
    assert data
    assert {point["source"] for point in data} == {"estimated"}  # CRG: Dashboard can label synthetic trend data.


def test_growth_estimates_are_stable_between_refreshes(client: TestClient) -> None:
    first = client.get(f"{API_PREFIX}/analysis/growth?days=3")
    second = client.get(f"{API_PREFIX}/analysis/growth?days=3")
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()  # CRG: Refreshing dashboard growth should not change estimates.
