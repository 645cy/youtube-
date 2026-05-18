"""
FastAPI 主应用入口

架构概览:
  - Lifespan 上下文管理器 (`_initialize_database`, `_seed_development_data`)
  - CORS 中间件配置
  - 6 个业务 Router 挂载
  - 健康检查端点 (`health_check`, `health_check_v1`)
  - SQLite WAL 模式初始化 (`init_db`)
  - 数据种子自动执行 (开发环境, `seed_all`)

路由挂载:
  /api/v1/channels       -> `apps.api.routers.channels`    (Channel CRUD)
  /api/v1/videos         -> `apps.api.routers.videos`      (Video CRUD + 筛选)
  /api/v1/analysis       -> `apps.api.routers.analysis`    (分析任务 + 爆款检测)
  /api/v1/radar          -> `apps.api.routers.radar`       (竞品雷达监控)
  /api/v1/lab            -> `apps.api.routers.lab`         (OCP实验室 用户画像+推荐)
  /api/v1/content-factory -> `apps.api.routers.content_factory` (内容工厂 选题/脚本/分镜)

依赖模块:
  - `packages.db.schema`    — 数据库初始化与连接管理
  - `apps.api.config`       — Pydantic Settings 配置读取
  - `apps.api.seed.seed_db` — 开发环境数据种子
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.bootstrap import (
    initialize_database,
    initialize_youtube_extractor,
    preload_recommender,
    seed_development_data,
    shutdown_resources,
    start_background_scheduler,
)
from apps.api.config import settings
from apps.api.routers import analysis, channels, content_factory, crawler, lab, projects, radar, videos

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("main")

API_PREFIX = settings.API_PREFIX


def register_routers(app: FastAPI) -> None:
    routers = [
        channels.router,
        videos.router,
        analysis.router,
        radar.router,
        lab.router,
        content_factory.router,
        crawler.router,
        projects.router,
    ]
    for router in routers:
        app.include_router(router, prefix=API_PREFIX)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("=== Application Startup ===")
    await initialize_database()
    await seed_development_data()
    preload_recommender(app)
    initialize_youtube_extractor(app)
    start_background_scheduler(app)
    logger.info("=== Startup Complete ===")
    yield
    logger.info("=== Application Shutdown ===")
    await shutdown_resources()
    logger.info("=== Shutdown Complete ===")


app = FastAPI(
    title="YouTube Monitor API",
    description="YouTube 竞品监控 + 爆款检测 + OCP 实验室 + 内容工厂",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Request-ID"],
)

register_routers(app)


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {"app": "YouTube Monitor API", "version": "1.0.0", "docs": "/docs"}


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str | bool | dict]:
    key_configured = bool(settings.YOUTUBE_API_KEY.strip())
    health = {
        "status": "ok",
        "env": settings.ENV,
        "database": "connected",
        "youtube_api_configured": key_configured,
        "youtube_api_reachable": False,
        "quota": {},
    }
    if settings.HEALTH_CHECK_YOUTUBE_QUOTA:
        try:
            extractor = getattr(app.state, "extractor", None)
            if extractor:
                quota_report = await extractor.quota.get_usage_report()
                health["youtube_api_reachable"] = True
                health["quota"] = quota_report
        except Exception as e:
            health["youtube_api_reachable"] = False
            health["quota_error"] = str(e)
    else:
        health["youtube_api_reachable"] = key_configured and getattr(app.state, "extractor", None) is not None
    return health


@app.get("/api/v1/health", tags=["Health"])
async def health_check_v1() -> dict[str, str | bool | dict]:
    return await health_check()


@app.get("/api/v1/integrations/youtube/diagnostics", tags=["Health"])
async def youtube_diagnostics(live_check: bool = False) -> dict:
    key = settings.YOUTUBE_API_KEY.strip()
    extractor = getattr(app.state, "extractor", None)
    result = {
        "configured": bool(key),
        "key_length": len(key) if key else 0,
        "extractor_ready": extractor is not None,
        "quota": {},
        "live_check": "skipped",
        "status": "needs_key" if not key else "configured",
        "next_action": "Add YOUTUBE_API_KEY to .env" if not key else "Run live check to verify API access",
    }
    if extractor:
        result["quota"] = await extractor.quota.get_usage_report()
    if live_check and extractor:
        try:
            probe = await asyncio.wait_for(extractor.search_channels("@mkbhd", max_results=1), timeout=10)
            ok = bool(probe.get("items"))
            result["live_check"] = "passed" if ok else "empty"
            result["status"] = "connected" if ok else "api_returned_empty"
            result["next_action"] = "YouTube API is ready" if ok else "Check API key restrictions and quota"
        except Exception as e:
            result["live_check"] = "failed"
            result["status"] = "unreachable"
            result["next_action"] = "Check YouTube Data API, quota, network, or proxy"
            result["error"] = f"{type(e).__name__}: {e}"
    return result
