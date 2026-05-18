"""
视频业务服务层 — 封装 Video 的数据库查询与 YouTube 数据解析.

被以下模块使用:
  - apps.api.routers.videos      (REST API 端点)
  - apps.api.routers.channels    (频道统计中的视频聚合)

设计决策:
  - 本层负责视频筛选条件构建、排序、ISO8601 时长解析、YouTube item 规范化.
  - Router 层保留 HTTP 参数校验和响应 shaping.
"""
from __future__ import annotations

import json
import re
from typing import Any

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.db.schema import Video


# ── 筛选与排序 ──

ALLOWED_VIDEO_SORT_FIELDS = {
    "published_at", "view_count", "like_count", "comment_count",
    "duration", "created_at", "updated_at", "title",
}


def build_video_filters(
    channel_id: int | None,
    is_short: bool | None,
    category_id: str | None,
    language: str | None,
    min_views: int | None,
    min_duration: int | None,
    max_duration: int | None,
) -> list[Any]:
    """构建视频列表的多维筛选条件列表.

    被 list_videos 和 dashboard 统计复用.
    """
    conditions = []
    if channel_id:
        conditions.append(Video.channel_id == channel_id)
    if is_short is not None:
        conditions.append(Video.is_short == is_short)
    if category_id:
        conditions.append(Video.category_id == category_id)
    if language:
        conditions.append(Video.language == language)
    if min_views is not None:
        conditions.append(Video.view_count >= min_views)
    if min_duration is not None:
        conditions.append(Video.duration >= min_duration)
    if max_duration is not None:
        conditions.append(Video.duration <= max_duration)
    return conditions


def apply_video_sorting(query: Any, sort_by: str, sort_order: str) -> Any:
    """为视频查询应用排序.

    Raises:
        ValueError: 当 sort_by 不在允许字段中时.
    """
    if sort_by not in ALLOWED_VIDEO_SORT_FIELDS:
        raise ValueError(
            f"Invalid sort_by field: '{sort_by}'. Allowed: {', '.join(sorted(ALLOWED_VIDEO_SORT_FIELDS))}"
        )
    sort_col = getattr(Video, sort_by, Video.published_at)
    return query.order_by(desc(sort_col) if sort_order == "desc" else sort_col)


# ── YouTube 数据解析 ──

def parse_iso8601_duration(duration: str | None) -> int | None:
    """解析 YouTube ISO8601 时长字符串 (PT1H2M3S) 为秒数."""
    if not duration:
        return None
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
    if not match:
        return None
    return int(match.group(1) or 0) * 3600 + int(match.group(2) or 0) * 60 + int(match.group(3) or 0)


def safe_int_stat(stats: dict[str, Any], key: str) -> int | None:
    """安全地从 YouTube statistics 字典中提取整数值."""
    value = stats.get(key)
    return int(value) if value else None


def build_video_from_youtube_item(item: dict[str, Any], channel_id: int) -> Video | None:
    """将 YouTube API video item 规范化为 Video 模型实例.

    Args:
        item: YouTube API videos.list 返回的单个 item.
        channel_id: 本地频道 ID (外键).

    Returns:
        Video 实例，或 None 当 item 缺少 id 时.
    """
    youtube_id = item.get("id", "")
    if not youtube_id:
        return None
    snippet = item.get("snippet", {})
    stats = item.get("statistics", {})
    duration_sec = parse_iso8601_duration(item.get("contentDetails", {}).get("duration"))
    return Video(
        youtube_id=youtube_id,
        channel_id=channel_id,
        title=snippet.get("title", "Unknown"),
        description=snippet.get("description"),
        thumbnail_url=snippet.get("thumbnails", {}).get("high", {}).get("url"),
        published_at=None,
        duration=duration_sec,
        view_count=safe_int_stat(stats, "viewCount"),
        like_count=safe_int_stat(stats, "likeCount"),
        comment_count=safe_int_stat(stats, "commentCount"),
        tags=json.dumps(snippet.get("tags", []), ensure_ascii=False) if snippet.get("tags") else None,
        category_id=snippet.get("categoryId"),
        is_short=duration_sec is not None and duration_sec <= 60,
    )


# ── 批量导入 ──

async def import_videos_from_items(
    session: AsyncSession,
    items: list[dict[str, Any]],
    channel_id: int,
) -> dict[str, int]:
    """批量将 YouTube API items 导入数据库，自动去重.

    Returns:
        {"imported": int, "skipped": int}
    """
    imported = 0
    skipped = 0

    for item in items:
        yid = item.get("id", "")
        video = build_video_from_youtube_item(item, channel_id)
        if not video:
            skipped += 1
            continue

        existing = await session.execute(
            select(Video).where(Video.youtube_id == yid)
        )
        if existing.scalar_one_or_none():
            skipped += 1
            continue

        session.add(video)
        imported += 1

    return {"imported": imported, "skipped": skipped}
