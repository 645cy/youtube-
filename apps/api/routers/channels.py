"""
频道管理 Router — CRUD + 搜索 + 统计
路由前缀: /api/v1/channels
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.schemas import ChannelCreate, ChannelList, ChannelRead, ChannelUpdate
from apps.api.config import settings
from packages.db.schema import Channel, Video, MetricHistory, MetricType, get_db_session

router = APIRouter(prefix="/channels", tags=["Channels"])


def _pick_thumbnail(snippet: dict | None) -> str | None:
    """从 YouTube snippet 中按质量优先级提取缩略图 URL."""
    if not snippet:
        return None
    thumbnails = snippet.get("thumbnails", {}) or {}
    for key in ("high", "medium", "default"):
        url = (thumbnails.get(key) or {}).get("url")
        if isinstance(url, str) and url.strip():
            return url.strip()
    return None


def _missing_thumbnail(value: str | None) -> bool:
    return not isinstance(value, str) or not value.strip()


@router.post("", response_model=ChannelRead, status_code=status.HTTP_201_CREATED)
async def create_channel(
    data: ChannelCreate,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Channel:
    """创建新频道记录."""
    # 检查 youtube_id 是否已存在
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
    """通过 DualTrackExtractor 搜索频道并入库.

    流程:
      1. DualTrackExtractor.search_channels() 查找频道 (API → yt-dlp → CrawlerEngine)
      2. DualTrackExtractor.get_channel_details() 获取详细统计
      3. 存入数据库 (去重: youtube_id)
      4. 返回 ChannelRead
    """
    # 先尝试本地数据库搜索
    local_result = await session.execute(
        select(Channel).where(Channel.title.ilike(f"%{query}%"))
    )
    local_channel = local_result.scalar_one_or_none()
    if local_channel:
        return local_channel

    # 使用双轨提取器搜索
    from apps.api.services.youtube_api import DualTrackExtractor
    extractor = DualTrackExtractor(api_key=settings.YOUTUBE_API_KEY)

    try:
        # CRG: Bound API/crawler fallback so channel search fails fast instead of hanging the UI.
        search_result = await asyncio.wait_for(
            extractor.search_channels(query, max_results=1),
            timeout=12,
        )
        items = search_result.get("items", [])
        if not items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No YouTube channel found for query: {query}",
            )

        snippet = items[0].get("snippet", {})
        youtube_id = snippet.get("channelId")
        # web 抓取可能没有 channelId，需要从 title 推断或返回错误
        if not youtube_id:
            # 尝试从 web 抓取的结果中查找 handle，然后获取频道 ID
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Could not resolve channel ID for query: {query}",
            )

        title = snippet.get("title", "Unknown")
        description = snippet.get("description")
        thumbnail_url = _pick_thumbnail(snippet)

        # 检查是否已存在
        existing = await session.execute(
            select(Channel).where(Channel.youtube_id == youtube_id)
        )
        channel = existing.scalar_one_or_none()
        if channel:
            return channel

        # 获取详细统计 (双轨: API → yt-dlp)
        detail_result = await extractor.get_channel_details([youtube_id])
        detail_items = detail_result.get("items", [])
        if detail_items:
            stats = detail_items[0].get("statistics", {})
            detail_snippet = detail_items[0].get("snippet", {})
            subscriber_count = int(stats["subscriberCount"]) if stats.get("subscriberCount") else None
            video_count = int(stats["videoCount"]) if stats.get("videoCount") else None
            view_count = int(stats["viewCount"]) if stats.get("viewCount") else None
            country = detail_snippet.get("country")
        else:
            subscriber_count = video_count = view_count = None
            country = None

        # 入库
        channel = Channel(
            youtube_id=youtube_id,
            title=title,
            description=description,
            subscriber_count=subscriber_count,
            video_count=video_count,
            view_count=view_count,
            thumbnail_url=thumbnail_url,
            country=country,
        )
        session.add(channel)
        await session.flush()
        await session.refresh(channel)

        # 写入初始指标历史，支撑增长曲线
        from datetime import timezone
        now = datetime.now(timezone.utc)
        if subscriber_count is not None:
            session.add(MetricHistory(
                channel_id=channel.id, metric_type=MetricType.SUBSCRIBER,
                value=float(subscriber_count), recorded_at=now,
            ))
        if view_count is not None:
            session.add(MetricHistory(
                channel_id=channel.id, metric_type=MetricType.VIEW,
                value=float(view_count), recorded_at=now,
            ))
        await session.flush()

        return channel

    except HTTPException:
        raise
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Channel search timed out. Check YouTube API access or configure a proxy.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Channel search unavailable: {type(e).__name__}. Please check network connection.",
        )


@router.get("/tags", response_model=list[dict[str, str | int]])
async def list_tags(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[dict[str, str | int]]:
    """获取所有热门标签 (从频道 niche 字段聚合)."""
    from sqlalchemy import func
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
    youtube_id: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Channel:
    """通过 YouTube ID 导入频道信息 (调用双轨 API)."""
    # 检查是否已存在
    existing = await session.execute(
        select(Channel).where(Channel.youtube_id == youtube_id)
    )
    existing_channel = existing.scalar_one_or_none()
    if existing_channel:
        return existing_channel

    # 使用双轨提取器获取频道数据
    from apps.api.services.youtube_api import DualTrackExtractor
    extractor = DualTrackExtractor(api_key=settings.YOUTUBE_API_KEY)
    result = await extractor.get_channel_details([youtube_id])

    items = result.get("items", [])
    if not items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"YouTube channel {youtube_id} not found",
        )

    item = items[0]
    snippet = item.get("snippet", {})
    stats = item.get("statistics", {})

    subscriber_count = int(stats.get("subscriberCount", 0)) if stats.get("subscriberCount") else None
    video_count = int(stats.get("videoCount", 0)) if stats.get("videoCount") else None
    view_count = int(stats.get("viewCount", 0)) if stats.get("viewCount") else None

    channel = Channel(
        youtube_id=youtube_id,
        title=snippet.get("title", "Unknown"),
        description=snippet.get("description"),
        subscriber_count=subscriber_count,
        video_count=video_count,
        view_count=view_count,
        thumbnail_url=_pick_thumbnail(snippet),
        country=snippet.get("country"),
    )
    session.add(channel)
    await session.flush()
    await session.refresh(channel)

    # 写入初始指标历史
    from datetime import timezone
    now = datetime.now(timezone.utc)
    if subscriber_count is not None:
        session.add(MetricHistory(
            channel_id=channel.id, metric_type=MetricType.SUBSCRIBER,
            value=float(subscriber_count), recorded_at=now,
        ))
    if view_count is not None:
        session.add(MetricHistory(
            channel_id=channel.id, metric_type=MetricType.VIEW,
            value=float(view_count), recorded_at=now,
        ))
    await session.flush()

    return channel


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
    extractor = DualTrackExtractor(api_key=settings.YOUTUBE_API_KEY)

    youtube_ids = [c.youtube_id for c in channels if c.youtube_id]
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
        thumb = _pick_thumbnail(snippet)
        if _missing_thumbnail(thumb):
            skipped += 1
            continue
        ch.thumbnail_url = thumb
        ch.updated_at = now
        updated += 1

    await session.flush()
    return {"scanned": len(channels), "updated": updated, "skipped": skipped}


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
    extractor = DualTrackExtractor(api_key=settings.YOUTUBE_API_KEY)

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

                # 检查是否已存在
                existing = await session.execute(
                    select(Channel).where(Channel.youtube_id == youtube_id)
                )
                if existing.scalar_one_or_none():
                    skipped += 1
                    continue

                # 获取详情
                detail = await extractor.get_channel_details([youtube_id])
                detail_items = detail.get("items", [])
                if not detail_items:
                    failed += 1
                    continue

                d = detail_items[0]
                stats = d.get("statistics", {})
                s = d.get("snippet", {})

                ch = Channel(
                    youtube_id=youtube_id,
                    title=s.get("title", snippet.get("title", "Unknown")),
                    description=s.get("description", snippet.get("description")),
                    subscriber_count=int(stats["subscriberCount"]) if stats.get("subscriberCount") else None,
                    video_count=int(stats["videoCount"]) if stats.get("videoCount") else None,
                    view_count=int(stats["viewCount"]) if stats.get("viewCount") else None,
                    thumbnail_url=_pick_thumbnail(s) or _pick_thumbnail(snippet),
                    country=s.get("country"),
                )
                session.add(ch)
                await session.flush()

                # metric_history
                from datetime import timezone
                now = datetime.now(timezone.utc)
                if ch.subscriber_count is not None:
                    session.add(MetricHistory(
                        channel_id=ch.id, metric_type=MetricType.SUBSCRIBER,
                        value=float(ch.subscriber_count), recorded_at=now,
                    ))
                if ch.view_count is not None:
                    session.add(MetricHistory(
                        channel_id=ch.id, metric_type=MetricType.VIEW,
                        value=float(ch.view_count), recorded_at=now,
                    ))

                imported += 1
                results.append({"youtube_id": youtube_id, "title": ch.title})
        except Exception as e:
            logger = logging.getLogger("channels")
            logger.warning(f"Bulk discover failed for '{keyword}': {e}")
            failed += 1

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
            thumb = _pick_thumbnail(snippet)
            if thumb:
                ch.thumbnail_url = thumb
                updated += 1
            else:
                failed += 1
        except Exception:
            failed += 1

    await session.flush()
    await session.commit()

    return {
        "checked": checked,
        "updated": updated,
        "failed": failed,
    }


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

    # 统计
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
