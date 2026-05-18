"""
频道业务服务层 — 封装 Channel 的数据库操作与 YouTube 数据同步.

被以下模块使用:
  - apps.api.routers.channels    (REST API 端点)
  - apps.api.seed.seed_db        (开发环境数据种子)

设计决策:
  - 本层负责所有与 Channel/MetricHistory 相关的数据库写入和 YouTube 数据规范化.
  - Router 层只保留 HTTP 参数校验、错误响应 shaping 和路由协调.
  - 避免 Router 直接操作 schema (见 CODE_INTELLIGENCE.md "Fat Router" 分析).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.db.schema import Channel, MetricHistory, MetricType

logger = logging.getLogger(__name__)


# ── 工具函数 ──

def pick_thumbnail(snippet: dict | None) -> str | None:
    """从 YouTube snippet 中按质量优先级提取缩略图 URL."""
    if not snippet:
        return None
    thumbnails = snippet.get("thumbnails", {}) or {}
    for key in ("high", "medium", "default"):
        url = (thumbnails.get(key) or {}).get("url")
        if isinstance(url, str) and url.strip():
            return url.strip()
    return None


def missing_thumbnail(value: str | None) -> bool:
    return not isinstance(value, str) or not value.strip()


def stat_int(stats: dict[str, Any], key: str) -> int | None:
    value = stats.get(key)
    return int(value) if value else None


# ── 数据规范化 ──

def build_channel_values(
    youtube_id: str,
    fallback_snippet: dict[str, Any],
    detail_item: dict[str, Any] | None,
) -> dict[str, Any]:
    """将 YouTube API 响应规范化为 Channel 模型字段字典.

    被 search_channels / import_from_youtube / bulk_discover 复用.
    """
    detail_snippet = (detail_item or {}).get("snippet", {})
    stats = (detail_item or {}).get("statistics", {})
    snippet = detail_snippet or fallback_snippet

    # 解析频道创建时间
    channel_created_at = None
    published_at = snippet.get("publishedAt")
    if published_at:
        from datetime import datetime
        try:
            channel_created_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        except ValueError:
            pass

    return {
        "youtube_id": youtube_id,
        "title": snippet.get("title", fallback_snippet.get("title", "Unknown")),
        "description": snippet.get("description", fallback_snippet.get("description")),
        "subscriber_count": stat_int(stats, "subscriberCount"),
        "video_count": stat_int(stats, "videoCount"),
        "view_count": stat_int(stats, "viewCount"),
        "thumbnail_url": pick_thumbnail(snippet) or pick_thumbnail(fallback_snippet),
        "country": snippet.get("country"),
        "channel_created_at": channel_created_at,
    }


# ── 数据库操作 ──

async def add_metric_history(session: AsyncSession, channel: Channel) -> None:
    """为频道创建初始指标历史记录 (导入/创建时调用)."""
    now = datetime.now(timezone.utc)
    if channel.subscriber_count is not None:
        session.add(MetricHistory(
            channel_id=channel.id,
            metric_type=MetricType.SUBSCRIBER,
            value=float(channel.subscriber_count),
            recorded_at=now,
        ))
    if channel.view_count is not None:
        session.add(MetricHistory(
            channel_id=channel.id,
            metric_type=MetricType.VIEW,
            value=float(channel.view_count),
            recorded_at=now,
        ))


async def get_channel_by_youtube_id(session: AsyncSession, youtube_id: str) -> Channel | None:
    """通过 YouTube 公开 ID 查询本地频道记录."""
    result = await session.execute(select(Channel).where(Channel.youtube_id == youtube_id))
    return result.scalar_one_or_none()


async def import_channel_from_youtube(
    session: AsyncSession,
    extractor: Any,
    youtube_id: str,
    fallback_snippet: dict[str, Any],
    require_detail: bool = False,
) -> Channel:
    """通过 DualTrackExtractor 获取频道详情并写入数据库.

    Args:
        extractor: DualTrackExtractor 实例 (避免循环导入，类型标注为 Any).
        require_detail: 为 True 时，如果 YouTube 返回空则抛出异常.

    Returns:
        已持久化的 Channel 实例 (尚未 commit，调用方负责).
    """
    detail_result = await extractor.get_channel_details([youtube_id])
    detail_items = detail_result.get("items", [])
    if require_detail and not detail_items:
        raise ValueError(f"YouTube channel {youtube_id} not found")

    channel = Channel(**build_channel_values(
        youtube_id,
        fallback_snippet,
        detail_items[0] if detail_items else None,
    ))
    session.add(channel)
    await session.flush()
    add_metric_history(session, channel)
    await session.flush()
    return channel


async def backfill_channel_thumbnails(
    session: AsyncSession,
    extractor: Any,
    channels: list[Channel],
) -> dict[str, int]:
    """批量回查 YouTube 并更新频道缩略图.

    Returns:
        {"updated": int, "skipped": int}
    """
    youtube_ids = [c.youtube_id for c in channels if c.youtube_id]
    if not youtube_ids:
        return {"updated": 0, "skipped": len(channels)}

    details = await extractor.get_channel_details(youtube_ids)
    items = details.get("items", []) if isinstance(details, dict) else []
    by_id: dict[str, dict] = {}
    for item in items:
        cid = (item.get("id") or "").strip()
        if cid:
            by_id[cid] = item

    updated = 0
    skipped = 0
    now = datetime.utcnow()
    for ch in channels:
        item = by_id.get(ch.youtube_id)
        if not item:
            skipped += 1
            continue
        snippet = item.get("snippet", {})
        thumb = pick_thumbnail(snippet)
        if missing_thumbnail(thumb):
            skipped += 1
            continue
        ch.thumbnail_url = thumb
        ch.updated_at = now
        updated += 1

    return {"updated": updated, "skipped": skipped}


async def repair_channel_thumbnails(
    session: AsyncSession,
    extractor: Any,
    channels: list[Channel],
) -> dict[str, int]:
    """逐个频道回查缩略图 (比批量更容错).

    Returns:
        {"checked": int, "updated": int, "failed": int}
    """
    checked = 0
    updated = 0
    failed = 0

    for ch in channels:
        checked += 1
        try:
            detail = await extractor.get_channel_details([ch.youtube_id])
            items = detail.get("items", [])
            if not items:
                failed += 1
                continue
            snippet = items[0].get("snippet", {})
            thumb = pick_thumbnail(snippet)
            if thumb:
                ch.thumbnail_url = thumb
                updated += 1
            else:
                failed += 1
        except Exception:
            failed += 1

    return {"checked": checked, "updated": updated, "failed": failed}
