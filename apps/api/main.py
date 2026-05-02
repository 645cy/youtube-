"""
FastAPI 主应用入口

架构概览:
  - Lifespan 上下文管理器 (启动/关闭事件)
  - CORS 中间件配置
  - 6 个业务 Router 挂载
  - 健康检查端点
  - SQLite WAL 模式初始化
  - 数据种子自动执行 (开发环境)

路由挂载:
  /api/v1/channels       -> Channel CRUD
  /api/v1/videos         -> Video CRUD + 筛选
  /api/v1/analysis       -> 分析任务 + 爆款检测
  /api/v1/radar          -> 竞品雷达监控
  /api/v1/lab            -> OCP实验室 (用户画像+推荐)
  /api/v1/content-factory -> 内容工厂 (选题/脚本/分镜)
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.config import settings
from packages.db.schema import close_db, init_db

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("main")


# ── Lifespan 上下文管理器 ──

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理.

    启动:
      1. 初始化数据库 (WAL 模式 + 建表)
      2. 开发环境自动执行数据种子
      3. 加载推荐引擎

    关闭:
      1. 关闭数据库连接
      2. 清理资源
    """
    logger.info("=== Application Startup ===")

    # 1. 数据库初始化
    try:
        await init_db(database_url=settings.DATABASE_URL, echo=settings.ECHO_SQL)
        logger.info("Database initialized (WAL mode)")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

    # 2. 开发环境自动种子（默认关闭，避免启动阶段阻塞）
    if settings.ENV == "development" and settings.AUTO_SEED_ON_STARTUP:
        try:
            from apps.api.seed.seed_db import seed_all
            await seed_all()
            logger.info("Development seed data applied")
        except Exception as e:
            logger.warning(f"Seed skipped (may already exist): {e}")

    # 3. 预加载推荐引擎
    try:
        from apps.api.services.recommender import load_default_paths, PathRecommender
        paths = load_default_paths()
        app.state.recommender = PathRecommender(paths=paths)
        logger.info(f"Recommender loaded with {len(paths)} monetization paths")
    except Exception as e:
        logger.warning(f"Recommender preload failed: {e}")
        if settings.ENV == "production":
            raise RuntimeError(f"Recommender preload failed in production: {e}") from e

    # 4. 预加载 YouTube API 双轨提取器
    try:
        from apps.api.services.youtube_api import DualTrackExtractor
        app.state.extractor = DualTrackExtractor(api_key=settings.YOUTUBE_API_KEY)
        logger.info("YouTube dual-track extractor initialized")
    except Exception as e:
        logger.warning(f"YouTube extractor init failed: {e}")
        if settings.ENV == "production":
            raise RuntimeError(f"YouTube extractor init failed in production: {e}") from e

    # 5. 启动后台定时调度器（默认关闭，避免无 API Key 时后台任务阻塞）
    if settings.START_SCHEDULER_ON_STARTUP:
        try:
            from apps.api.services.scheduler import init_scheduler
            scheduler = init_scheduler()
            app.state.scheduler = scheduler
            logger.info("Background scheduler initialized")
        except Exception as e:
            logger.warning(f"Scheduler init failed: {e}")
            if settings.ENV == "production":
                raise RuntimeError(f"Scheduler init failed in production: {e}") from e

    logger.info("=== Startup Complete ===")
    yield

    # 关闭
    logger.info("=== Application Shutdown ===")
    try:
        from apps.api.services.scheduler import shutdown_scheduler
        shutdown_scheduler()
    except Exception:
        logger.exception("Scheduler shutdown failed")
    await close_db()
    logger.info("Database connections closed")
    logger.info("=== Shutdown Complete ===")


# ── FastAPI 应用实例 ──

app = FastAPI(
    title="YouTube Monitor API",
    description="YouTube 竞品监控 + 爆款检测 + OCP 实验室 + 内容工厂",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS 中间件 ──

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENV == "development" else (
        [settings.FRONTEND_URL] if settings.FRONTEND_URL else []
    ) + [
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Request-ID"],
)

# ── Router 挂载 ──

from apps.api.routers import channels, videos, analysis, radar, lab, content_factory, crawler  # noqa: E402

app.include_router(channels.router, prefix=f"{settings.API_PREFIX}")
app.include_router(videos.router, prefix=f"{settings.API_PREFIX}")
app.include_router(analysis.router, prefix=f"{settings.API_PREFIX}")
app.include_router(radar.router, prefix=f"{settings.API_PREFIX}")
app.include_router(lab.router, prefix=f"{settings.API_PREFIX}")
app.include_router(content_factory.router, prefix=f"{settings.API_PREFIX}")
app.include_router(crawler.router, prefix=f"{settings.API_PREFIX}")


# ── 根端点 ──

@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {
        "app": "YouTube Monitor API",
        "version": "1.0.0",
        "docs": "/docs",
    }


# ── 健康检查 ──

@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str | bool | dict]:
    """服务健康检查端点.

    返回:
      - status: ok/error
      - env: 当前环境
      - youtube_api: API 可用状态
      - quota: 配额使用状态
    """
    health = {
        "status": "ok",
        "env": settings.ENV,
        "database": "connected",
        "youtube_api": False,
        "quota": {},
    }

    # 检查 YouTube API 状态
    if settings.HEALTH_CHECK_YOUTUBE_QUOTA:
        try:
            extractor = getattr(app.state, "extractor", None)
            if extractor:
                quota_report = await extractor.quota.get_usage_report()
                health["youtube_api"] = True
                health["quota"] = quota_report
        except Exception as e:
            health["youtube_api"] = False
            health["quota_error"] = str(e)
    else:
        health["youtube_api"] = bool(settings.YOUTUBE_API_KEY)

    return health


@app.get("/api/v1/health", tags=["Health"])
async def health_check_v1() -> dict[str, str | bool | dict]:
    """API v1 健康检查 (与根健康检查一致)."""
    return await health_check()


@app.get("/api/v1/integrations/youtube/diagnostics", tags=["Health"])
async def youtube_diagnostics(live_check: bool = False) -> dict:
    """Return YouTube integration state without exposing secrets."""
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
            # CRG: Keep live validation bounded so the settings page cannot hang on network failures.
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
