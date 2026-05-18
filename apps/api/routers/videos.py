"""
视频管理 Router — CRUD + 高级筛选 + 批量导入
路由前缀: /api/v1/videos

职责边界:
  - 本层只负责 HTTP 参数校验、错误响应 shaping、路由协调.
  - 所有数据库查询条件和 YouTube 数据解析委托给 video_service.
  - 见 CODE_INTELLIGENCE.md "Fat Router" 优化记录.
"""
from __future__ import annotations

import json
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.schemas import VideoCreate, VideoList, VideoRead
from apps.api.config import settings
from apps.api.services.video_service import (
    ALLOWED_VIDEO_SORT_FIELDS,
    apply_video_sorting,
    build_video_filters,
    build_video_from_youtube_item,
    import_videos_from_items,
)
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

    dump = data.model_dump()
    if isinstance(dump.get("tags"), list):
        dump["tags"] = json.dumps(dump["tags"], ensure_ascii=False)
    video = Video(**dump)
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
    from sqlalchemy import and_

    query = select(Video)
    count_query = select(Video.id)  # 使用 select().subquery() 模式避免 func.count 问题

    conditions = build_video_filters(
        channel_id, is_short, category_id, language, min_views, min_duration, max_duration
    )
    if conditions:
        filter_condition = and_(*conditions)
        query = query.where(filter_condition)
        # count_query 也需要同样条件，但使用 func.count 更简洁

    try:
        query = apply_video_sorting(query, sort_by, sort_order).offset(offset).limit(limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    result = await session.execute(query)

    # 独立计数查询
    from sqlalchemy import func
    count_base = select(func.count(Video.id))
    if conditions:
        count_base = count_base.where(filter_condition)
    count_result = await session.execute(count_base)

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
    youtube_ids: Annotated[list[str], Body()],
    channel_id: Annotated[int, Query(ge=1)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    """批量导入视频 (通过 YouTube API 或 yt-dlp)."""
    from apps.api.services.youtube_api import DualTrackExtractor
    extractor = DualTrackExtractor(api_key=settings.YOUTUBE_API_KEY)
    try:
        result = await extractor.get_video_details(youtube_ids)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch video details: {e}",
        )

    items = result.get("items", [])
    stats = await import_videos_from_items(session, items, channel_id)

    return {
        **stats,
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
