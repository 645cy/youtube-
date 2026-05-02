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
    YOUTUBE_API_KEY: str = ""
    FORCE_YTDLP_MODE: bool = False  # 强制使用 yt-dlp 降级，不走 API
    API_QUOTA_LIMIT: int = 10_000  # 每日配额上限 (单位)

    # 爬虫配置
    CRAWLER_MIN_DELAY_MS: int = 1_500
    CRAWLER_MAX_DELAY_MS: int = 4_500
    CRAWLER_MAX_RETRIES: int = 5
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
    API_PREFIX: str = "/api/v1"
    AUTO_SEED_ON_STARTUP: bool = False
    START_SCHEDULER_ON_STARTUP: bool = False
    HEALTH_CHECK_YOUTUBE_QUOTA: bool = False
    FETCH_REMOTE_COMMENTS_FOR_ANALYSIS: bool = False

    # 业务默认值
    DEFAULT_NICHE: str = "ai_tools"
    DEFAULT_TARGET_REGION: str = "global"
    DEFAULT_VIDEO_TYPE: str = "tutorial"
    DEFAULT_CRAWLER_TASK_TYPE: str = "channel_latest"
    DEFAULT_CRAWLER_FREQUENCY: str = "manual"
    DEFAULT_MONITOR_FREQUENCY: str = "daily"
    CRAWLER_DEFAULT_MAX_RESULTS: int = 10
    RADAR_TRIGGER_MAX_RESULTS: int = 5
    ANALYSIS_REMOTE_COMMENTS_LIMIT: int = 20

    @property
    def proxy_list(self) -> list[str]:
        if not self.CRAWLER_PROXY_LIST:
            return []
        return [p.strip() for p in self.CRAWLER_PROXY_LIST.split(",") if p.strip()]


settings = Settings()
