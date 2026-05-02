"""Test fixtures and configuration."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

# Override settings BEFORE importing main so lifespan uses memory DB
from apps.api.config import settings

settings.DATABASE_URL = "sqlite+aiosqlite:///:memory:"
settings.ENV = "development"
settings.START_SCHEDULER_ON_STARTUP = False
settings.AUTO_SEED_ON_STARTUP = False
settings.HEALTH_CHECK_YOUTUBE_QUOTA = False

from apps.api.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client() -> TestClient:
    with TestClient(app) as c:
        yield c
