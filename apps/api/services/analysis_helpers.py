"""
Analysis Router 辅助函数 — 提取自 analysis.py 以减少 Router 层复杂度.

被以下模块使用:
  - apps.api.routers.analysis    (REST API 端点)
  - apps.api.routers.channels    (频道统计 / 增长数据)

设计决策:
  - 本层负责 niche 评分的数据聚合、增长趋势的查询与估算、远程评论获取.
  - Router 层保留 HTTP 错误处理和响应 shaping.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import case, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.db.schema import Channel, MetricHistory, MetricType, Video

logger = logging.getLogger(__name__)


# ── Niche Scoring Helpers ──

async def resolve_niche_name(session: AsyncSession, request_target_type: str, request_target_id: str) -> str:
    """将分析请求的目标解析为 niche 名称字符串."""
    if request_target_type == "niche":
        return request_target_id
    result = await session.execute(select(Video).where(Video.youtube_id == request_target_id))
    video = result.scalar_one_or_none()
    return video.title[:30] if video else request_target_id


async def load_niche_channels(session: AsyncSession, niche_name: str) -> list[Channel]:
    """加载指定 niche 的频道列表；若无匹配则返回全部频道."""
    result = await session.execute(select(Channel).where(Channel.niche == niche_name))
    channels = list(result.scalars().all())
    if channels:
        return channels
    fallback = await session.execute(select(Channel))
    return list(fallback.scalars().all())


async def estimate_evergreen_ratio(session: AsyncSession, channels: list[Channel]) -> float:
    """基于频道视频标题关键词估算 evergreen 内容比例."""
    if not channels:
        return 0.4
    result = await session.execute(
        select(Video).where(Video.channel_id.in_([c.id for c in channels])).limit(100)
    )
    videos = list(result.scalars().all())
    if not videos:
        return 0.4
    evergreen_keywords = [
        "how to", "tutorial", "guide", "beginner",
        "complete", "step by step", "basics", "explained",
    ]
    evergreen_count = sum(
        1 for video in videos
        if any(keyword in (video.title or "").lower() for keyword in evergreen_keywords)
    )
    return round(evergreen_count / len(videos), 2)


# ── Growth Trend Helpers ──

async def load_metric_growth_rows(
    session: AsyncSession,
    since: datetime,
    minimum_points: int,
) -> list[dict[str, Any]]:
    """从 MetricHistory 加载按日聚合的订阅/观看增长数据."""
    mh_result = await session.execute(
        select(
            func.date(MetricHistory.recorded_at).label("date"),
            func.sum(
                case((MetricHistory.metric_type == MetricType.SUBSCRIBER, MetricHistory.value), else_=0)
            ).label("subscribers"),
            func.sum(case((MetricHistory.metric_type == MetricType.VIEW, MetricHistory.value), else_=0)).label("views"),
        )
        .where(MetricHistory.recorded_at >= since)
        .group_by(func.date(MetricHistory.recorded_at))
        .order_by(func.date(MetricHistory.recorded_at))
    )
    rows = mh_result.all()
    if not rows or len(rows) < minimum_points:
        return []
    return [
        {
            "date": str(r.date),
            "source": "metric_history",
            "subscribers": int(r.subscribers or 0),
            "views": int(r.views or 0),
            "videos": 0,
        }
        for r in rows
    ]


async def load_growth_totals(session: AsyncSession) -> tuple[int, int, int]:
    """返回当前全平台总订阅、总观看、总视频数."""
    ch_result = await session.execute(select(func.sum(Channel.subscriber_count), func.sum(Channel.view_count)))
    total_subs, total_views = ch_result.one_or_none() or (0, 0)
    v_result = await session.execute(select(func.count(Video.id)))
    total_videos = v_result.scalar() or 0
    return int(total_subs or 0), int(total_views or 0), int(total_videos or 0)


def build_estimated_growth_rows(
    days: int,
    total_subs: int,
    total_views: int,
    total_videos: int,
) -> list[dict[str, Any]]:
    """基于当前总量生成平滑的估算增长趋势（当历史数据不足时回退使用）."""
    today = datetime.now(timezone.utc).date()
    result = []
    for i in range(days, -1, -1):
        progress = 1 - (i / max(days, 1))
        result.append({
            "date": (today - timedelta(days=i)).strftime("%Y-%m-%d"),
            "source": "estimated",
            "subscribers": max(0, int(total_subs * (progress ** 1.5))),
            "views": max(0, int(total_views * (progress ** 1.3))),
            "videos": max(0, int(total_videos * (progress ** 1.2))),
        })
    return result


# ── Remote Comment Fetcher ──

async def fetch_video_comments(youtube_id: str, limit: int = 20) -> list[tuple[str, str]]:
    """通过 DualTrackExtractor 获取 YouTube 视频评论.

    Raises:
        RuntimeError: 当远程评论获取失败时.
    """
    try:
        from apps.api.services.youtube_api import DualTrackExtractor
        from apps.api.config import settings
        extractor = DualTrackExtractor(api_key=settings.YOUTUBE_API_KEY)
        return await extractor.get_comments(
            youtube_id,
            max_results=limit or settings.ANALYSIS_REMOTE_COMMENTS_LIMIT,
        )
    except Exception as e:
        logger.warning(f"Remote comments fetch failed for {youtube_id}: {e}")
        raise RuntimeError(f"Remote comments unavailable: {type(e).__name__}") from e
