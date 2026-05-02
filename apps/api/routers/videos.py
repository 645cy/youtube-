"""
视频管理 Router — CRUD + 高级筛选 + 批量导入
路由前缀: /api/v1/videos
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.schemas import VideoCreate, VideoList, VideoRead
from apps.api.config import settings
from packages.db.schema import Channel, Video, get_db_session

router = APIRouter(prefix="/videos", tags=["Videos"])


@router.post("", response_model=VideoRead, status_code=status.HTTP_201_CREATED)
async def create_video(
    data: VideoCreate,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Video:
    """创建视频记录."""
    # 验证频道存在
    ch_result = await session.execute(select(Channel).where(Channel.id == data.channel_id))
    if not ch_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Channel {data.channel_id} not found",
        )
    # 检查重复
    existing = await session.execute(
        select(Video).where(Video.youtube_id == data.youtube_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Video {data.youtube_id} already exists",
        )

    video = Video(**data.model_dump())
    session.add(video)
    await session.flush()
    await session.refresh(video)
    return video


@router.get("", response_model=VideoList)
async def list_videos(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    channel_id: Annotated[int | None, Query()] = None,
    is_short: Annotated[bool | None, Query()] = None,
    category_id: Annotated[str | None, Query()] = None,
    language: Annotated[str | None, Query()] = None,
    min_views: Annotated[int | None, Query(ge=0)] = None,
    min_duration: Annotated[int | None, Query(ge=0)] = None,
    max_duration: Annotated[int | None, Query(ge=0)] = None,
    sort_by: Annotated[str, Query()] = "published_at",
    sort_order: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
) -> dict:
    """视频列表 (支持多维筛选和排序)."""
    query = select(Video)
    count_query = select(func.count(Video.id))

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

    if conditions:
        filter_condition = and_(*conditions)
        query = query.where(filter_condition)
        count_query = count_query.where(filter_condition)

    # 排序
    sort_col = getattr(Video, sort_by, Video.published_at)
    if sort_order == "desc":
        query = query.order_by(desc(sort_col))
    else:
        query = query.order_by(sort_col)

    query = query.offset(offset).limit(limit)

    result = await session.execute(query)
    count_result = await session.execute(count_query)

    return {
        "items": result.scalars().all(),
        "total": count_result.scalar(),
        "offset": offset,
        "limit": limit,
    }


@router.get("/{video_id}", response_model=VideoRead)
async def get_video(
    video_id: int,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Video:
    """获取视频详情."""
    result = await session.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video {video_id} not found",
        )
    return video


@router.post("/import-batch", status_code=status.HTTP_201_CREATED)
async def import_videos_batch(
    youtube_ids: list[str],
    channel_id: int,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    """批量导入视频 (通过 YouTube API 或 yt-dlp)."""
    from apps.api.services.youtube_api import DualTrackExtractor
    extractor = DualTrackExtractor(api_key=settings.YOUTUBE_API_KEY)
    result = await extractor.get_video_details(youtube_ids)

    items = result.get("items", [])
    imported = 0
    skipped = 0

    for item in items:
        yid = item.get("id", "")
        # 检查是否已存在
        existing = await session.execute(
            select(Video).where(Video.youtube_id == yid)
        )
        if existing.scalar_one_or_none():
            skipped += 1
            continue

        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        cd = item.get("contentDetails", {})
        duration = cd.get("duration")
        duration_sec = None
        if duration:
            import re
            m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
            if m:
                duration_sec = (int(m.group(1) or 0) * 3600 +
                               int(m.group(2) or 0) * 60 +
                               int(m.group(3) or 0))

        video = Video(
            youtube_id=yid,
            channel_id=channel_id,
            title=snippet.get("title", "Unknown"),
            description=snippet.get("description"),
            thumbnail_url=snippet.get("thumbnails", {}).get("high", {}).get("url"),
            published_at=None,
            duration=duration_sec,
            view_count=int(stats.get("viewCount", 0)) if stats.get("viewCount") else None,
            like_count=int(stats.get("likeCount", 0)) if stats.get("likeCount") else None,
            comment_count=int(stats.get("commentCount", 0)) if stats.get("commentCount") else None,
            tags=json.dumps(snippet.get("tags", [])) if snippet.get("tags") else None,
            category_id=snippet.get("categoryId"),
            is_short=duration_sec is not None and duration_sec <= 60,
        )
        session.add(video)
        imported += 1

    await session.flush()
    return {
        "imported": imported,
        "skipped": skipped,
        "total": len(youtube_ids),
        "source": result.get("source", "api"),
    }


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
    video_id: int,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """删除视频."""
    result = await session.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video {video_id} not found",
        )
    await session.delete(video)
