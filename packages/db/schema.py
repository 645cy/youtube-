"""
SQLAlchemy 2.0 完整模型定义 — 五表关联架构

表清单:
  - `Channel`: 频道信息
  - `Video`: 视频信息 (FK->Channel)
  - `MonitorJob`: 监控任务 (FK->Channel)
  - `AnalysisLog`: 分析日志 (FK->Video)
  - `MetricHistory`: 指标历史 (FK->Channel)

被以下模块直接使用:
  - `apps.api.routers.channels`    — 频道 CRUD + 统计
  - `apps.api.routers.videos`      — 视频 CRUD + 筛选
  - `apps.api.routers.analysis`    — 分析日志写入
  - `apps.api.routers.radar`       — 监控任务调度
  - `apps.api.services.channel_service` — 频道导入/缩略图回填
  - `apps.api.services.analysis.*` — 分析算法结果持久化
  - `apps.api.seed.seed_db`        — 开发环境数据种子
  - `apps.api.services.scheduler`  — 调度引擎读写

设计决策:
  - 使用 AsyncAttrs + DeclarativeBase 支持异步 ORM
  - Mapped[] + mapped_column 类型安全声明
  - 整数自增主键用于内部关联, youtube_id 用于外部查询
  - WAL 模式初始化函数
"""
from __future__ import annotations

import os

import enum
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, List, Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# ── 工具函数 ──

def now_utc() -> datetime:
    return datetime.now(timezone.utc)


# ── 枚举定义 ──

class MonitorStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    ARCHIVED = "archived"


class JobType(str, enum.Enum):
    STATS = "stats"
    NEW_VIDEOS = "new_videos"
    COMMENTS = "comments"
    SEARCH = "search"


class AnalysisType(str, enum.Enum):
    VIRAL_DETECTION = "viral_detection"
    EVERGREEN = "evergreen"
    SENTIMENT = "sentiment"
    MONETIZATION = "monetization"
    NICHE_SCORE = "niche_score"


class MetricType(str, enum.Enum):
    SUBSCRIBER = "subscriber"
    VIEW = "view"
    LIKE = "like"
    COMMENT = "comment"


class CrawlerTaskStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class CrawlerRunStatus(str, enum.Enum):
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"


# ── 基础模型 ──

class Base(AsyncAttrs, DeclarativeBase):
    """SQLAlchemy 2.0 异步基类."""

    type_annotation_map: dict[type, type] = {
        dict[str, Any]: JSON,
        list[str]: JSON,
    }


# ── 频道表 ──

class Channel(Base):
    """YouTube 频道信息表.

    设计决策:
      - youtube_id: YouTube 公开频道 ID (如 UCxxxx)
      - subscriber_count/video_count/view_count 存储最新快照
      - 统计变化历史由 MetricHistory 记录
    """
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    youtube_id: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    subscriber_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    video_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    view_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    niche: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # ── 频道发现字段 (Channel Discovery) ──
    channel_created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="YouTube 频道创建时间"
    )
    avg_views_per_video: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True, comment="频道平均播放量 (总播放/视频数)"
    )
    discovery_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="潜力评分 0-100"
    )
    discovery_keyword: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="发现该频道的关键词"
    )
    discovered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="首次发现时间"
    )
    last_stats_updated: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="统计信息最后更新时间"
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc
    )

    # 关系
    videos: Mapped[List["Video"]] = relationship(
        back_populates="channel",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    monitor_jobs: Mapped[List["MonitorJob"]] = relationship(
        back_populates="channel",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    metric_history: Mapped[List["MetricHistory"]] = relationship(
        back_populates="channel",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


# ── 视频表 ──

class Video(Base):
    """YouTube 视频信息表.

    设计决策:
      - youtube_id: 11 字符公开视频 ID
      - channel_id -> Channel.id 外键
      - duration 以秒存储 (避免 timedelta 跨平台问题)
      - tags 以 JSON 字符串存储
      - is_short 自动判断 (时长<=60s 或 #shorts 标签)
    """
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    youtube_id: Mapped[str] = mapped_column(String(11), unique=True, index=True)
    channel_id: Mapped[int] = mapped_column(
        ForeignKey("channels.id", ondelete="CASCADE"), index=True
    )

    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 秒
    view_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    like_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    comment_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list
    category_id: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    is_short: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    # 关系
    channel: Mapped["Channel"] = relationship(back_populates="videos")
    analysis_logs: Mapped[List["AnalysisLog"]] = relationship(
        back_populates="video",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # 索引优化
    __table_args__ = (
        Index("ix_videos_channel_published", "channel_id", "published_at"),
    )


# ── 监控任务表 ──

class MonitorJob(Base):
    """监控任务配置表.

    一个频道可以有多个监控任务 (每日统计、新视频检测等).
    config_json 存储灵活的任务参数 (如筛选条件、关键词等).
    """
    __tablename__ = "monitor_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column(
        ForeignKey("channels.id", ondelete="CASCADE"), index=True
    )

    job_type: Mapped[JobType] = mapped_column(String(20), default=JobType.STATS)
    frequency: Mapped[str] = mapped_column(String(20), default="daily")  # daily|hourly|weekly
    status: Mapped[MonitorStatus] = mapped_column(String(10), default=MonitorStatus.ACTIVE)

    last_run_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_run_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    config_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON 序列化配置

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    # 关系
    channel: Mapped["Channel"] = relationship(back_populates="monitor_jobs")


class CrawlerTask(Base):
    """Reusable crawler task configuration."""
    __tablename__ = "crawler_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(160))
    task_type: Mapped[str] = mapped_column(String(40), default="channel_latest")
    target: Mapped[str] = mapped_column(String(500))
    frequency: Mapped[str] = mapped_column(String(20), default="manual")
    status: Mapped[str] = mapped_column(String(20), default=CrawlerTaskStatus.ACTIVE)
    config_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    runs: Mapped[List["CrawlerTaskRun"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class CrawlerTaskRun(Base):
    """Append-only crawler task execution record."""
    __tablename__ = "crawler_task_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("crawler_tasks.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(20), default=CrawlerRunStatus.RUNNING)
    source_status: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    items_found: Mapped[int] = mapped_column(Integer, default=0)
    result_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    task: Mapped["CrawlerTask"] = relationship(back_populates="runs")

    __table_args__ = (
        Index("ix_crawler_runs_task_started", "task_id", "started_at"),
    )


# ── 分析日志表 ──

class AnalysisLog(Base):
    """分析任务执行日志表.

    append-only 设计，记录每次分析的结果。
    result_json 存储灵活的 JSON 分析结果。
    """
    __tablename__ = "analysis_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    video_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("videos.id", ondelete="CASCADE"), nullable=True, index=True
    )
    channel_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("channels.id", ondelete="SET NULL"), nullable=True, index=True
    )

    analysis_type: Mapped[AnalysisType] = mapped_column(String(30))
    result_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    # 关系
    video: Mapped[Optional["Video"]] = relationship(back_populates="analysis_logs")


# ── 指标历史表 ──

class MetricHistory(Base):
    """频道/视频指标历史记录表 (时间序列数据).

    每条记录是一个时间点的指标快照。
    单表 + 索引设计，支撑百万级记录。
    """
    __tablename__ = "metric_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("channels.id", ondelete="CASCADE"), nullable=True, index=True
    )
    video_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("videos.id", ondelete="CASCADE"), nullable=True, index=True
    )

    metric_type: Mapped[MetricType] = mapped_column(String(20))
    value: Mapped[float] = mapped_column(Float)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    # 关系
    channel: Mapped[Optional["Channel"]] = relationship(back_populates="metric_history")

    # 索引
    __table_args__ = (
        Index("ix_metrics_channel_type_recorded", "channel_id", "metric_type", "recorded_at"),
        Index("ix_metrics_video_recorded", "video_id", "recorded_at"),
    )


# ── 频道发现结果表 ──

class ChannelDiscoveryResult(Base):
    """单次发现任务的详细结果快照.

    用于审计和回溯某次任务的具体发现。
    主要数据仍由 Channel 表维护，此表做 append-only 记录。
    """
    __tablename__ = "channel_discovery_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    crawler_task_run_id: Mapped[int] = mapped_column(
        ForeignKey("crawler_task_runs.id", ondelete="CASCADE"), index=True
    )
    channel_id: Mapped[int] = mapped_column(
        ForeignKey("channels.id", ondelete="CASCADE"), index=True
    )
    keyword: Mapped[str] = mapped_column(String(200))
    viral_score: Mapped[float] = mapped_column(Float)
    rank: Mapped[int] = mapped_column(Integer, default=0)  # 本次任务内排名

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


# ── 内容项目表 ──

class ContentProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class ContentProject(Base):
    """内容项目表 — 串联 Crawler → Factory → Lab 工作流.

    一个项目对应一次完整的内容创作流程：
    从爬虫抓取数据 → 生成脚本/分镜 → 分析优化 → 变现路径规划。
    """
    __tablename__ = "content_projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=ContentProjectStatus.DRAFT)

    # 来源 — 从哪次爬虫任务/执行创建
    source_crawler_task_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("crawler_tasks.id", ondelete="SET NULL"), nullable=True, index=True
    )
    source_run_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("crawler_task_runs.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Factory 产出
    script_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    storyboard_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Lab 分析结果
    analysis_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    monetization_path_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc
    )

    # 关系
    source_task: Mapped[Optional["CrawlerTask"]] = relationship(
        "CrawlerTask", foreign_keys=[source_crawler_task_id]
    )
    source_run: Mapped[Optional["CrawlerTaskRun"]] = relationship(
        "CrawlerTaskRun", foreign_keys=[source_run_id]
    )

    __table_args__ = (
        Index("ix_projects_status_updated", "status", "updated_at"),
    )


# ── 数据库引擎与会话管理 ──

_engine = None
_SessionLocal = None


def get_engine(database_url: str | None = None, echo: bool = False) -> Any:
    """获取或创建异步数据库引擎 (单例)."""
    global _engine
    if _engine is None:
        url = database_url or os.environ.get("DATABASE_URL") or "sqlite+aiosqlite:///./data/tubefactory.db"
        _engine = create_async_engine(url, echo=echo, pool_pre_ping=True)
    return _engine


def get_sessionmaker() -> Any:
    """获取异步 Session 工厂."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _SessionLocal


async def init_db(
    database_url: str | None = None,
    echo: bool = False,
    create_missing_tables: bool = True,
) -> None:
    """初始化数据库: WAL 模式 + 建表."""
    engine = get_engine(database_url, echo)
    async with engine.begin() as conn:
        # SQLite WAL 模式 (读写并发性能提升 10x+)
        await conn.exec_driver_sql("PRAGMA journal_mode=WAL")
        await conn.exec_driver_sql("PRAGMA synchronous=NORMAL")
        await conn.exec_driver_sql("PRAGMA foreign_keys=ON")
        await conn.exec_driver_sql("PRAGMA temp_store=MEMORY")
        await conn.exec_driver_sql("PRAGMA cache_size=-64000")
        if create_missing_tables:
            # CRG: Keep local/dev startup convenient while production uses Alembic migrations.
            await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """关闭数据库引擎."""
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI Depends 用的异步 Session 生成器.

    每个请求创建独立 Session, 成功自动 commit, 异常自动 rollback.
    """
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


