"""
Pydantic Settings - 环境变量配置管理
统一管理数据库、YouTube API、爬虫、日志等配置
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置 (支持 .env 文件覆盖)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 数据库
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/tubefactory.db"
    ECHO_SQL: bool = False

    # YouTube API
    YOUTUBE_API_KEY: str = ""  # 支持单 Key 或逗号分隔多 Key: key1,key2,key3
    FORCE_YTDLP_MODE: bool = False  # 强制使用 yt-dlp 降级，不走 API
    API_QUOTA_LIMIT: int = 10_000  # 每个 Key 每日配额上限 (单位)

    @property
    def youtube_api_keys(self) -> list[str]:
        """解析逗号分隔的多 API Key，去重去空."""
        raw = self.YOUTUBE_API_KEY or ""
        keys = [k.strip() for k in raw.split(",") if k.strip()]
        # 去重保持顺序
        seen = set()
        unique = []
        for k in keys:
            if k not in seen:
                seen.add(k)
                unique.append(k)
        return unique

    # 代理配置
    PROXY_URL: str = ""  # 如 http://127.0.0.1:7890
    PROXY_AUTO_DETECT: bool = True  # 启动时自动探测代理

    # 爬虫配置
    CRAWLER_MIN_DELAY_MS: int = 1_500
    CRAWLER_MAX_DELAY_MS: int = 4_500
    CRAWLER_MAX_RETRIES: int = 2  # 5 次太多，代理失败时快速返回
    CRAWLER_MAX_CONCURRENCY: int = 3
    CRAWLER_MAX_REQ_PER_MINUTE: int = 15
    CRAWLER_USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    CRAWLER_PROXY_LIST: str = ""  # 逗号分隔代理列表
    CRAWLER_BACKOFF_BASE: float = 2.0
    CRAWLER_BACKOFF_MAX: float = 60.0

    # 应用
    LOG_LEVEL: str = "INFO"
    ENV: str = "development"  # development | production
    FRONTEND_URL: str = ""  # 生产环境前端域名，如 https://tubefactory.example.com
    ALLOWED_ORIGINS: str = ""  # CRG: Production CORS origins must be explicit and environment-driven.
    API_PREFIX: str = "/api/v1"
    AUTO_CREATE_TABLES_ON_STARTUP: bool = False  # CRG: Production should use Alembic instead of implicit create_all.
    AUTO_SEED_ON_STARTUP: bool = False
    START_SCHEDULER_ON_STARTUP: bool = True
    HEALTH_CHECK_YOUTUBE_QUOTA: bool = False
    FETCH_REMOTE_COMMENTS_FOR_ANALYSIS: bool = False
    # CRG: Bound blocking YouTube client work instead of using the default executor.
    YOUTUBE_BLOCKING_MAX_WORKERS: int = 4
    # CRG: Persist quota usage across service restarts.
    YOUTUBE_QUOTA_STATE_PATH: str = "./data/youtube_quota_state.json"

    # 业务默认值 — 移除硬编码，强制用户选择或从环境变量读取
    DEFAULT_NICHE: str = ""  # 不再硬编码 ai_tools，空值表示未配置
    DEFAULT_TARGET_REGION: str = "global"
    DEFAULT_VIDEO_TYPE: str = ""  # 不再硬编码 tutorial
    DEFAULT_CRAWLER_TASK_TYPE: str = "keyword_search"  # 新用户首选：无需先有本地频道
    DEFAULT_CRAWLER_FREQUENCY: str = "manual"
    DEFAULT_MONITOR_FREQUENCY: str = "daily"
    CRAWLER_DEFAULT_MAX_RESULTS: int = 25  # 10 条太少，实用性不足
    RADAR_TRIGGER_MAX_RESULTS: int = 10
    ANALYSIS_REMOTE_COMMENTS_LIMIT: int = 20

    @property
    def allowed_origins(self) -> list[str]:
        if self.ENV == "development":
            return ["*"]
        origins = [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]
        if self.FRONTEND_URL:
            origins.append(self.FRONTEND_URL.strip())
        # CRG: De-duplicate configured production origins without keeping localhost fallbacks.
        return list(dict.fromkeys(origins))


settings = Settings()
