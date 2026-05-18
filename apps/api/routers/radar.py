"""
竞品雷达监控 Router
路由前缀: /api/v1/radar

功能:
  - 竞品频道监控 (新视频检测)
  - 差异化比对 (view/like/comment 多维对比)
  - 监控任务 CRUD
  - 定时调度配置
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.schemas import MonitorJobCreate, MonitorJobRead, MonitorJobUpdate, MonitorWithChannel
from apps.api.services.analyzer import SchedulerEngine
from apps.api.config import settings
from packages.db.schema import (
    Channel,
    CrawlerRunStatus,
    CrawlerTask,
    CrawlerTaskRun,
    MonitorJob,
    Video,
    get_db_session,
)

router = APIRouter(prefix="/radar", tags=["Radar"])


@router.post("/monitors", response_model=MonitorJobRead, status_code=status.HTTP_201_CREATED)
async def create_monitor(
    data: MonitorJobCreate,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MonitorJob:
    """创建竞品监控任务."""
    # 验证频道存在
    ch_result = await session.execute(select(Channel).where(Channel.id == data.channel_id))
    channel = ch_result.scalar_one_or_none()
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Channel {data.channel_id} not found",
        )

    existing_result = await session.execute(
        select(MonitorJob).where(
            MonitorJob.channel_id == data.channel_id,
            MonitorJob.job_type == data.job_type,
        )
    )
    existing_job = existing_result.scalar_one_or_none()
    if existing_job:
        return existing_job

    job = MonitorJob(
        channel_id=data.channel_id,
        job_type=data.job_type,
        frequency=data.frequency,
        config_json=data.config_json,
        next_run_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    session.add(job)
    await session.flush()
    await session.refresh(job)
    return job


@router.get("/monitors", response_model=list[MonitorWithChannel])
async def list_monitors(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    channel_id: Annotated[int | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
) -> list[MonitorWithChannel]:
    """列出监控任务，包含关联频道信息."""
    from packages.db.schema import Channel

    query = (
        select(MonitorJob, Channel)
        .join(Channel, MonitorJob.channel_id == Channel.id, isouter=True)
        .order_by(desc(MonitorJob.created_at))
    )
    if channel_id:
        query = query.where(MonitorJob.channel_id == channel_id)
    if status:
        query = query.where(MonitorJob.status == status)

    result = await session.execute(query)
    rows = result.all()

    items: list[MonitorWithChannel] = []
    for job, ch in rows:
        items.append(MonitorWithChannel(
            id=job.id,
            channel_id=job.channel_id,
            channel_name=ch.title if ch else "未命名",
            channel_thumbnail=(ch.thumbnail_url or "") if ch else "",
            subscriber_count=(ch.subscriber_count or 0) if ch else 0,
            job_type=str(job.job_type),
            frequency=job.frequency,
            status=str(job.status),
            last_run_at=job.last_run_at,
            next_run_at=job.next_run_at,
            created_at=job.created_at,
        ))
    return items


@router.get("/monitors/{job_id}", response_model=MonitorJobRead)
async def get_monitor(
    job_id: int,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MonitorJob:
    """获取监控任务详情."""
    result = await session.execute(select(MonitorJob).where(MonitorJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail=f"Monitor job {job_id} not found")
    return job


@router.put("/monitors/{job_id}", response_model=MonitorJobRead)
async def update_monitor(
    job_id: int,
    data: MonitorJobUpdate,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MonitorJob:
    """更新监控任务."""
    result = await session.execute(select(MonitorJob).where(MonitorJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail=f"Monitor job {job_id} not found")

    if data.frequency:
        job.frequency = data.frequency
    if data.status:
        job.status = data.status
    if data.config_json:
        job.config_json = data.config_json
    if data.next_run_at:
        job.next_run_at = data.next_run_at

    await session.flush()
    await session.refresh(job)
    return job


@router.delete("/monitors/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_monitor(
    job_id: int,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """删除监控任务."""
    result = await session.execute(select(MonitorJob).where(MonitorJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail=f"Monitor job {job_id} not found")
    await session.delete(job)


@router.post("/monitors/{job_id}/trigger")
async def trigger_monitor(
    job_id: int,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    """手动触发监控任务 (获取频道最新视频)."""
    job = await _load_monitor_job(session, job_id)
    channel = await _load_monitor_channel(session, job.channel_id)
    source_status, source_message, api_items = await _fetch_monitor_upload_items(channel)
    new_videos = await _extract_new_radar_videos(session, api_items)

    # 更新任务执行时间
    _refresh_monitor_schedule(job)
    crawler_task, crawler_run = await _record_radar_crawler_run(
        session, job, channel, source_status, source_message, new_videos
    )
    # CRG: Trigger route now orchestrates helpers instead of owning fetch/parsing/persistence branches.

    return {
        "job_id": job_id,
        "crawler_task_id": crawler_task.id,
        "crawler_run_id": crawler_run.id,
        "channel_title": channel.title if channel else "Unknown",
        "source_status": source_status,
        "message": source_message,
        "new_videos_found": len(new_videos),
        "new_videos": new_videos,
        "next_run_at": job.next_run_at.isoformat() if job.next_run_at else None,
    }


async def _load_monitor_job(session: AsyncSession, job_id: int) -> MonitorJob:
    result = await session.execute(select(MonitorJob).where(MonitorJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail=f"Monitor job {job_id} not found")
    return job


async def _load_monitor_channel(session: AsyncSession, channel_id: int) -> Channel:
    result = await session.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail=f"Channel {channel_id} not found")
    return channel


async def _fetch_monitor_upload_items(channel: Channel) -> tuple[str, str, list[dict[str, Any]]]:
    uploads_playlist_id = f"UU{channel.youtube_id[2:]}" if channel.youtube_id.startswith("UC") else None
    if not settings.YOUTUBE_API_KEY:
        return "skipped", "YOUTUBE_API_KEY is not configured; monitor timestamp was refreshed without remote fetch.", []
    if not uploads_playlist_id:
        return "skipped", "Channel youtube_id is not a UC channel id; uploads playlist cannot be derived.", []

    try:
        from apps.api.services.youtube_api import DualTrackExtractor
        extractor = DualTrackExtractor(api_key=settings.YOUTUBE_API_KEY)
        api_result = await extractor._api.playlist_items_list(
            uploads_playlist_id,
            max_results=settings.RADAR_TRIGGER_MAX_RESULTS,
        )
        # CRG: Isolate external YouTube fetch so trigger persistence stays testable.
        return "youtube_api", "", api_result.get("items", [])
    except Exception as exc:
        return "api_error", str(exc), []


async def _extract_new_radar_videos(
    session: AsyncSession,
    api_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    new_videos = []
    for item in api_items:
        snippet = item.get("snippet", {})
        video_id = snippet.get("resourceId", {}).get("videoId", "")
        if not video_id:
            continue
        existing = await session.execute(select(Video).where(Video.youtube_id == video_id))
        if existing.scalar_one_or_none():
            continue
        # CRG: Keep duplicate filtering in one helper before writing crawler-run evidence.
        new_videos.append({
            "youtube_id": video_id,
            "title": snippet.get("title", ""),
            "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url"),
            "published_at": snippet.get("publishedAt"),
        })
    return new_videos


def _refresh_monitor_schedule(job: MonitorJob) -> None:
    job.last_run_at = datetime.utcnow()
    job.next_run_at = SchedulerEngine.calculate_next_run(job.last_run_at, 60, 2.0)


async def _ensure_crawler_task_for_monitor(
    session: AsyncSession,
    job: MonitorJob,
    channel: Channel,
) -> CrawlerTask:
    result = await session.execute(
        select(CrawlerTask).where(
            CrawlerTask.task_type == "channel_latest",
            CrawlerTask.target == channel.youtube_id,
        )
    )
    task = result.scalar_one_or_none()
    if task:
        return task

    task = CrawlerTask(
        name=f"Radar latest videos: {channel.title}",
        task_type="channel_latest",
        target=channel.youtube_id,
        frequency=job.frequency or settings.DEFAULT_MONITOR_FREQUENCY,
        config_json=json.dumps(
            {"source": "radar_monitor", "monitor_job_id": job.id, "channel_id": channel.id},
            ensure_ascii=False,
        ),
    )
    session.add(task)
    await session.flush()
    await session.refresh(task)
    return task


async def _record_radar_crawler_run(
    session: AsyncSession,
    job: MonitorJob,
    channel: Channel,
    source_status: str,
    source_message: str,
    new_videos: list[dict[str, Any]],
) -> tuple[CrawlerTask, CrawlerTaskRun]:
    crawler_task = await _ensure_crawler_task_for_monitor(session, job, channel)
    crawler_payload = {
        "source_status": source_status,
        "message": source_message,
        "items": new_videos,
        "monitor_job_id": job.id,
        "channel_id": channel.id,
        "channel_title": channel.title,
    }
    crawler_run = CrawlerTaskRun(
        task_id=crawler_task.id,
        status=CrawlerRunStatus.SUCCESS,
        source_status=source_status,
        message=source_message or f"Radar check completed for {channel.title}.",
        items_found=len(new_videos),
        result_json=json.dumps(crawler_payload, ensure_ascii=False),
        finished_at=datetime.utcnow(),
    )
    session.add(crawler_run)
    crawler_task.last_run_at = crawler_run.finished_at
    await session.flush()
    await session.refresh(crawler_run)
    # CRG: Store every manual trigger as a crawler run even when remote fetch is skipped.
    return crawler_task, crawler_run


@router.get("/compare")
async def compare_channels(
    channel_ids: Annotated[list[int], Query(min_length=2, max_length=5)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    """竞品频道多维对比分析."""
    from sqlalchemy import func

    channels = []
    for cid in channel_ids:
        result = await session.execute(select(Channel).where(Channel.id == cid))
        ch = result.scalar_one_or_none()
        if ch:
            # 获取频道最新 5 个视频
            v_result = await session.execute(
                select(Video)
                .where(Video.channel_id == cid)
                .order_by(desc(Video.published_at))
                .limit(5)
            )
            videos = v_result.scalars().all()

            avg_views = await session.scalar(
                select(func.avg(Video.view_count))
                .where(Video.channel_id == cid)
            )

            channels.append({
                "id": ch.id,
                "title": ch.title,
                "subscriber_count": ch.subscriber_count,
                "video_count": ch.video_count,
                "total_views": ch.view_count,
                "avg_views_per_video": round(avg_views or 0, 2),
                "latest_videos": [
                    {"id": v.id, "title": v.title[:60], "views": v.view_count}
                    for v in videos
                ],
            })

    # 计算排名
    if len(channels) >= 2:
        sorted_by_subs = sorted(channels, key=lambda x: x["subscriber_count"] or 0, reverse=True)
        sorted_by_views = sorted(channels, key=lambda x: x["total_views"] or 0, reverse=True)
        leader = sorted_by_subs[0]
    else:
        sorted_by_subs = sorted_by_views = channels
        leader = channels[0] if channels else None

    return {
        "channels": channels,
        "channel_count": len(channels),
        "ranking_by_subscribers": [{"id": c["id"], "title": c["title"]} for c in sorted_by_subs],
        "ranking_by_views": [{"id": c["id"], "title": c["title"]} for c in sorted_by_views],
        "leader": leader,
        "analysis_summary": (
            f"共对比 {len(channels)} 个频道, 领先者: {leader['title'] if leader else 'N/A'}"
            if leader else "无数据"
        ),
    }


@router.get("/monitors/{job_id}/logs")
async def get_monitor_logs(
    job_id: int,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[dict[str, Any]]:
    """获取监控任务执行日志."""
    # 返回最近的执行记录 (通过 AnalysisLog 关联)
    result = await session.execute(select(MonitorJob).where(MonitorJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail=f"Monitor job {job_id} not found")

    from packages.db.schema import AnalysisLog
    logs_result = await session.execute(
        select(AnalysisLog)
        .where(AnalysisLog.channel_id == job.channel_id)
        .order_by(desc(AnalysisLog.created_at))
        .limit(limit)
    )
    logs = logs_result.scalars().all()
    return [
        {
            "id": log.id,
            "analysis_type": log.analysis_type,
            "score": log.score,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]
