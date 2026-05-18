"""
频道管理 Router — CRUD + 搜索 + 统计 + 批量导入
路由前缀: /api/v1/channels

职责边界:
  - 本层只负责 HTTP 参数校验、错误响应 shaping、路由协调.
  - 所有数据库操作和 YouTube 数据同步委托给 channel_service.
  - 见 CODE_INTELLIGENCE.md "Fat Router" 优化记录.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.schemas import ChannelCreate, ChannelList, ChannelRead, ChannelUpdate
from apps.api.config import settings
from apps.api.services.channel_service import (
    backfill_channel_thumbnails,
    get_channel_by_youtube_id,
    import_channel_from_youtube,
    repair_channel_thumbnails,
)
from packages.db.schema import Channel, Video, get_db_session

router = APIRouter(prefix="/channels", tags=["Channels"])
logger = logging.getLogger(__name__)


def _ensure_youtube_api_key() -> str:
    key = settings.YOUTUBE_API_KEY.strip()
    if not key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="YouTube API key is not configured. Set YOUTUBE_API_KEY or use ytdlp fallback.",
        )
    return key


def _first_search_snippet(search_result: dict[str, Any], query: str) -> tuple[str, dict[str, Any]]:
    """从 YouTube 搜索结果中提取第一个频道的 ID 和 snippet.

    Raises:
        HTTPException: 404 当搜索结果为空或无法解析频道 ID 时.
    """
    items = search_result.get("items", [])
    if not items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No YouTube channel found for query: {query}",
        )
    snippet = items[0].get("snippet", {})
    youtube_id = snippet.get("channelId")
    if not youtube_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not resolve channel ID for query: {query}",
        )
    return youtube_id, snippet


@router.post("", response_model=ChannelRead, status_code=status.HTTP_201_CREATED)
async def create_channel(
    data: ChannelCreate,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Channel:
    """创建新频道记录."""
    existing = await session.execute(
        select(Channel).where(Channel.youtube_id == data.youtube_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Channel with youtube_id={data.youtube_id} already exists",
        )

    channel = Channel(**data.model_dump())
    session.add(channel)
    await session.flush()
    await session.refresh(channel)
    return channel


@router.get("", response_model=ChannelList)
async def list_channels(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    search: Annotated[str | None, Query(max_length=100)] = None,
    niche: Annotated[str | None, Query()] = None,
    country: Annotated[str | None, Query(min_length=2, max_length=2)] = None,
    min_subscribers: Annotated[int | None, Query(ge=0)] = None,
) -> dict:
    """频道列表 (支持分页、搜索、筛选)."""
    query = select(Channel)
    count_query = select(func.count(Channel.id))

    if search:
        pattern = f"%{search}%"
        query = query.where(Channel.title.ilike(pattern))
        count_query = count_query.where(Channel.title.ilike(pattern))
    if niche:
        query = query.where(Channel.niche == niche)
        count_query = count_query.where(Channel.niche == niche)
    if country:
        query = query.where(Channel.country == country)
        count_query = count_query.where(Channel.country == country)
    if min_subscribers is not None:
        query = query.where(Channel.subscriber_count >= min_subscribers)
        count_query = count_query.where(Channel.subscriber_count >= min_subscribers)

    query = query.order_by(desc(Channel.updated_at)).offset(offset).limit(limit)

    result = await session.execute(query)
    count_result = await session.execute(count_query)

    items = result.scalars().all()
    total = count_result.scalar()

    return {
        "items": items,
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@router.post("/search", response_model=ChannelRead)
async def search_channels(
    query: Annotated[str, Query(min_length=1, max_length=100)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Channel:
    """通过 DualTrackExtractor 搜索频道、去重并入库."""
    # 先尝试本地数据库搜索
    local_result = await session.execute(
        select(Channel).where(Channel.title.ilike(f"%{query}%"))
    )
    local_channel = local_result.scalar_one_or_none()
    if local_channel:
        return local_channel

    # 使用双轨提取器搜索
    from apps.api.services.youtube_api import DualTrackExtractor
    extractor = DualTrackExtractor(api_key=_ensure_youtube_api_key())

    try:
        search_result = await asyncio.wait_for(
            extractor.search_channels(query, max_results=1),
            timeout=12,
        )
        youtube_id, snippet = _first_search_snippet(search_result, query)

        channel = await get_channel_by_youtube_id(session, youtube_id)
        if channel:
            return channel

        channel = await import_channel_from_youtube(session, extractor, youtube_id, snippet)
        await session.refresh(channel)
        return channel

    except HTTPException:
        raise
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Channel search timed out. Check YouTube API access or configure a proxy.",
        )
    except Exception as e:
        logger.warning(f"Channel search unavailable for '{query}': {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Channel search unavailable: {type(e).__name__}. Please check network connection.",
        )


@router.get("/tags", response_model=list[dict[str, str | int]])
async def list_tags(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[dict[str, str | int]]:
    """获取所有热门标签 (从频道 niche 字段聚合)."""
    result = await session.execute(
        select(Channel.niche, func.count(Channel.id).label("count"))
        .where(Channel.niche.isnot(None))
        .group_by(Channel.niche)
        .order_by(func.count(Channel.id).desc())
    )
    return [
        {"name": niche, "count": count, "trend": "stable"}
        for niche, count in result.all()
    ]


@router.post("/import-youtube", response_model=ChannelRead, status_code=status.HTTP_201_CREATED)
async def import_from_youtube(
    youtube_id: Annotated[str, Query(min_length=1)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Channel:
    """通过 YouTube ID 导入频道信息 (调用双轨 API)."""
    existing_channel = await get_channel_by_youtube_id(session, youtube_id)
    if existing_channel:
        return existing_channel

    from apps.api.services.youtube_api import DualTrackExtractor
    extractor = DualTrackExtractor(api_key=_ensure_youtube_api_key())
    try:
        channel = await import_channel_from_youtube(
            session, extractor, youtube_id, {}, require_detail=True
        )
        await session.refresh(channel)
        return channel
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Failed to import channel {youtube_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch channel from YouTube.",
        )


@router.post("/backfill-thumbnails")
async def backfill_thumbnails(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: Annotated[int, Query(ge=1, le=300)] = 100,
) -> dict:
    """为缺失频道头像的记录批量回填 thumbnail_url（真实 YouTube 数据）."""
    result = await session.execute(
        select(Channel)
        .where((Channel.thumbnail_url.is_(None)) | (Channel.thumbnail_url == ""))
        .order_by(desc(Channel.updated_at))
        .limit(limit)
    )
    channels = result.scalars().all()

    if not channels:
        return {"scanned": 0, "updated": 0, "skipped": 0}

    from apps.api.services.youtube_api import DualTrackExtractor
    extractor = DualTrackExtractor(api_key=_ensure_youtube_api_key())

    try:
        stats = await backfill_channel_thumbnails(session, extractor, channels)
        await session.flush()
        return {"scanned": len(channels), **stats}
    except Exception as e:
        logger.warning(f"Thumbnail backfill failed: {e}")
        return {"scanned": len(channels), "updated": 0, "skipped": 0, "error": str(e)}


@router.post("/bulk-discover", status_code=status.HTTP_201_CREATED)
async def bulk_discover(
    keywords: Annotated[list[str], Body()],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    max_per_keyword: Annotated[int, Query(ge=1, le=10)] = 3,
) -> dict:
    """批量发现频道 — 输入关键词列表，自动搜索、导入、去重.

    示例:
        POST /channels/bulk-discover
        ["AI make money", "passive income", "ChatGPT business"]
    """
    from apps.api.services.youtube_api import DualTrackExtractor
    extractor = DualTrackExtractor(api_key=_ensure_youtube_api_key())

    imported = 0
    skipped = 0
    failed = 0
    results = []

    for keyword in keywords:
        try:
            search_result = await extractor.search_channels(keyword, max_results=max_per_keyword)
            items = search_result.get("items", [])

            for item in items:
                snippet = item.get("snippet", {})
                youtube_id = snippet.get("channelId")
                if not youtube_id:
                    continue

                if await get_channel_by_youtube_id(session, youtube_id):
                    skipped += 1
                    continue

                ch = await import_channel_from_youtube(session, extractor, youtube_id, snippet)
                imported += 1
                results.append({"youtube_id": youtube_id, "title": ch.title})
        except Exception as e:
            logger.warning(f"Bulk discover failed for '{keyword}': {e}")
            failed += 1
            await session.rollback()

    await session.commit()
    return {
        "imported": imported,
        "skipped": skipped,
        "failed": failed,
        "channels": results,
    }


@router.post("/repair-thumbnails")
async def repair_channel_thumbnails(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
) -> dict:
    """补全历史空头像：为 thumbnail_url 为空的频道回查 YouTube 并更新."""
    from apps.api.services.youtube_api import DualTrackExtractor
    extractor = DualTrackExtractor(api_key=settings.YOUTUBE_API_KEY)

    q = await session.execute(
        select(Channel)
        .where((Channel.thumbnail_url.is_(None)) | (Channel.thumbnail_url == ""))
        .order_by(Channel.updated_at.desc())
        .limit(limit)
    )
    channels = q.scalars().all()

    try:
        stats = await repair_channel_thumbnails(session, extractor, channels)
        await session.flush()
        await session.commit()
        return stats
    except Exception as e:
        logger.warning(f"Thumbnail repair failed: {e}")
        return {"updated": 0, "failed": len(channels), "error": str(e)}


@router.get("/{channel_id}", response_model=ChannelRead)
async def get_channel(
    channel_id: int,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Channel:
    """获取指定频道详情."""
    result = await session.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Channel {channel_id} not found",
        )
    return channel


@router.put("/{channel_id}", response_model=ChannelRead)
async def update_channel(
    channel_id: int,
    data: ChannelUpdate,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Channel:
    """更新频道信息 (部分更新)."""
    result = await session.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Channel {channel_id} not found",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field_name, value in update_data.items():
        setattr(channel, field_name, value)

    await session.flush()
    await session.refresh(channel)
    return channel


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(
    channel_id: int,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """删除频道 (级联删除关联视频/任务/指标)."""
    result = await session.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Channel {channel_id} not found",
        )
    await session.delete(channel)


@router.get("/{channel_id}/stats")
async def get_channel_stats(
    channel_id: int,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    """获取频道统计概览 (视频数/总观看/平均表现)."""
    result = await session.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Channel {channel_id} not found",
        )

    video_count = await session.scalar(
        select(func.count(Video.id)).where(Video.channel_id == channel_id)
    )
    total_views = await session.scalar(
        select(func.sum(Video.view_count)).where(Video.channel_id == channel_id)
    )
    avg_views = await session.scalar(
        select(func.avg(Video.view_count)).where(Video.channel_id == channel_id)
    )

    return {
        "channel_id": channel_id,
        "channel_title": channel.title,
        "video_count": video_count or 0,
        "total_views": total_views or 0,
        "avg_views_per_video": round(avg_views or 0, 2),
        "subscriber_count": channel.subscriber_count,
        "subscriber_to_view_ratio": round(
            (channel.subscriber_count or 0) / max(total_views or 1, 1), 4
        ),
    }
