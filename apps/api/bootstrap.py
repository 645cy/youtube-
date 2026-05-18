from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI

from apps.api.config import settings
from packages.db.schema import close_db, init_db

logger = logging.getLogger(__name__)


async def initialize_database() -> None:
    try:
        await init_db(
            database_url=settings.DATABASE_URL,
            echo=settings.ECHO_SQL,
            create_missing_tables=settings.ENV == "development" or settings.AUTO_CREATE_TABLES_ON_STARTUP,
        )
        logger.info("Database initialized (WAL mode)")
    except Exception as exc:
        logger.error("Database initialization failed: %s", exc)
        raise


async def seed_development_data() -> None:
    if settings.ENV == "development" and settings.AUTO_SEED_ON_STARTUP:
        try:
            from apps.api.seed.seed_db import seed_all

            await seed_all()
            logger.info("Development seed data applied")
        except Exception as exc:
            logger.warning("Seed skipped (may already exist): %s", exc)


def preload_recommender(app: FastAPI) -> None:
    try:
        from apps.api.services.recommender import PathRecommender, load_default_paths

        paths = load_default_paths()
        app.state.recommender = PathRecommender(paths=paths)
        logger.info("Recommender loaded with %s monetization paths", len(paths))
    except Exception as exc:
        logger.warning("Recommender preload failed: %s", exc)
        if settings.ENV == "production":
            raise RuntimeError(f"Recommender preload failed in production: {exc}") from exc


def initialize_youtube_extractor(app: FastAPI) -> None:
    try:
        from apps.api.services.youtube_api import DualTrackExtractor

        app.state.extractor = DualTrackExtractor(api_key=settings.YOUTUBE_API_KEY)
        logger.info("YouTube dual-track extractor initialized")
    except Exception as exc:
        logger.warning("YouTube extractor init failed: %s", exc)
        if settings.ENV == "production":
            raise RuntimeError(f"YouTube extractor init failed in production: {exc}") from exc


def start_background_scheduler(app: FastAPI) -> None:
    if settings.START_SCHEDULER_ON_STARTUP:
        try:
            from apps.api.services.scheduler import init_scheduler

            scheduler = init_scheduler()
            app.state.scheduler = scheduler
            logger.info("Background scheduler initialized")
        except Exception as exc:
            logger.warning("Scheduler init failed: %s", exc)
            if settings.ENV == "production":
                raise RuntimeError(f"Scheduler init failed in production: {exc}") from exc


async def shutdown_resources() -> None:
    try:
        from apps.api.services.scheduler import shutdown_scheduler

        shutdown_scheduler()
    except Exception:
        logger.exception("Scheduler shutdown failed")

    try:
        from apps.api.services.youtube_api import close_youtube_executor

        close_youtube_executor()
    except Exception:
        logger.exception("YouTube executor shutdown failed")

    await close_db()
    logger.info("Database connections closed")
