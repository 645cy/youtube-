"""Smoke tests for seed_db, demo_cleanup, and import_trending scripts."""
from __future__ import annotations

import inspect

import pytest

from apps.api.seed import demo_cleanup, import_trending, seed_db


def test_seed_all_is_async_entrypoint() -> None:
    # CRG: Seed script should expose an awaitable entry point for startup integration.
    assert inspect.iscoroutinefunction(seed_db.seed_all)


def test_demo_cleanup_has_deterministic_title_set() -> None:
    assert "MrBeast" in demo_cleanup.DEMO_CHANNEL_TITLES
    assert len(demo_cleanup.DEMO_CHANNEL_TITLES) == len(set(demo_cleanup.DEMO_CHANNEL_TITLES))


@pytest.mark.anyio
async def test_import_trending_main_skips_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(import_trending, "YOUTUBE_API_KEY", "")
    # CRG: Import script must exit without network calls when no YouTube key is configured.
    assert await import_trending.main() is None
