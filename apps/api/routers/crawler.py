from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.config import settings
from apps.api.schemas import CrawlerTaskCreate, CrawlerTaskRead, CrawlerTaskRunRead
from packages.db.schema import (
    Channel,
    CrawlerRunStatus,
    CrawlerTask,
    CrawlerTaskRun,
    get_db_session,
)

router = APIRouter(prefix="/crawler", tags=["Crawler"])


def _task_read(task: CrawlerTask, latest_run: CrawlerTaskRun | None = None) -> CrawlerTaskRead:
    return CrawlerTaskRead(
        id=task.id,
        name=task.name,
        task_type=task.task_type,
        target=task.target,
        frequency=task.frequency,
        status=task.status,
        config_json=task.config_json,
        last_run_at=task.last_run_at,
        next_run_at=task.next_run_at,
        created_at=task.created_at,
        updated_at=task.updated_at,
        latest_run_status=latest_run.status if latest_run else None,
        latest_run_message=latest_run.message if latest_run else None,
        latest_items_found=latest_run.items_found if latest_run else 0,
    )


@router.post("/tasks", response_model=CrawlerTaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    data: CrawlerTaskCreate,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CrawlerTaskRead:
    task = CrawlerTask(
        name=data.name,
        task_type=data.task_type or settings.DEFAULT_CRAWLER_TASK_TYPE,
        target=data.target,
        frequency=data.frequency or settings.DEFAULT_CRAWLER_FREQUENCY,
        config_json=json.dumps(data.config, ensure_ascii=False) if data.config else None,
    )
    session.add(task)
    await session.flush()
    await session.refresh(task)
    return _task_read(task)


@router.get("/tasks", response_model=list[CrawlerTaskRead])
async def list_tasks(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    task_type: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[CrawlerTaskRead]:
    query = select(CrawlerTask).order_by(desc(CrawlerTask.created_at)).limit(limit)
    if task_type:
        query = query.where(CrawlerTask.task_type == task_type)
    result = await session.execute(query)
    tasks = result.scalars().all()

    items: list[CrawlerTaskRead] = []
    for task in tasks:
        run_result = await session.execute(
            select(CrawlerTaskRun)
            .where(CrawlerTaskRun.task_id == task.id)
            .order_by(desc(CrawlerTaskRun.started_at))
            .limit(1)
        )
        items.append(_task_read(task, run_result.scalar_one_or_none()))
    return items


@router.get("/tasks/{task_id}", response_model=CrawlerTaskRead)
async def get_task(
    task_id: int,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CrawlerTaskRead:
    result = await session.execute(select(CrawlerTask).where(CrawlerTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail=f"Crawler task {task_id} not found")

    run_result = await session.execute(
        select(CrawlerTaskRun)
        .where(CrawlerTaskRun.task_id == task.id)
        .order_by(desc(CrawlerTaskRun.started_at))
        .limit(1)
    )
    return _task_read(task, run_result.scalar_one_or_none())


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    result = await session.execute(select(CrawlerTask).where(CrawlerTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail=f"Crawler task {task_id} not found")
    await session.delete(task)


@router.post("/tasks/{task_id}/trigger", response_model=CrawlerTaskRunRead)
async def trigger_task(
    task_id: int,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CrawlerTaskRun:
    result = await session.execute(select(CrawlerTask).where(CrawlerTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail=f"Crawler task {task_id} not found")

    run = CrawlerTaskRun(task_id=task.id, status=CrawlerRunStatus.RUNNING)
    session.add(run)
    await session.flush()

    try:
        payload = await _execute_task(task, session)
        run.status = CrawlerRunStatus.SUCCESS
        run.source_status = payload["source_status"]
        run.message = payload["message"]
        run.items_found = len(payload["items"])
        run.result_json = json.dumps(payload, ensure_ascii=False)
    except Exception as exc:
        logger.exception(f"Crawler task {task.id} execution failed")
        run.status = CrawlerRunStatus.ERROR
        run.source_status = "error"
        run.message = str(exc)
        run.items_found = 0
        run.result_json = json.dumps({"error": str(exc)}, ensure_ascii=False)
    finally:
        now = datetime.now(timezone.utc)
        run.finished_at = now
        task.last_run_at = now

    await session.flush()
    await session.refresh(run)
    return run


@router.get("/tasks/{task_id}/runs", response_model=list[CrawlerTaskRunRead])
async def list_task_runs(
    task_id: int,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
) -> list[CrawlerTaskRun]:
    task_result = await session.execute(select(CrawlerTask.id).where(CrawlerTask.id == task_id))
    if task_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail=f"Crawler task {task_id} not found")

    result = await session.execute(
        select(CrawlerTaskRun)
        .where(CrawlerTaskRun.task_id == task_id)
        .order_by(desc(CrawlerTaskRun.started_at))
        .limit(limit)
    )
    return list(result.scalars().all())


async def _execute_task(task: CrawlerTask, session: AsyncSession) -> dict[str, Any]:
    if task.task_type == "channel_latest":
        return await _execute_channel_latest(task, session)
    if task.task_type == "channel_stats":
        return await _execute_channel_stats(task, session)
    if task.task_type == "keyword_search":
        return await _execute_keyword_search(task)
    return {"source_status": "skipped", "message": f"Unsupported task type: {task.task_type}", "items": []}


async def _execute_channel_latest(task: CrawlerTask, session: AsyncSession) -> dict[str, Any]:
    channel = await _resolve_channel(task.target, session)
    if not channel:
        return {"source_status": "not_found", "message": "No matching local channel found.", "items": []}

    uploads_playlist_id = f"UU{channel.youtube_id[2:]}" if channel.youtube_id.startswith("UC") else None
    if not uploads_playlist_id:
        return {"source_status": "skipped", "message": "Target is not a UC channel id.", "items": []}
    if not settings.YOUTUBE_API_KEY:
        return {"source_status": "skipped", "message": "YOUTUBE_API_KEY is not configured.", "items": []}

    try:
        from apps.api.services.youtube_api import DualTrackExtractor

        extractor = DualTrackExtractor(api_key=settings.YOUTUBE_API_KEY)
        api_result = await extractor._api.playlist_items_list(
            uploads_playlist_id,
            max_results=settings.CRAWLER_DEFAULT_MAX_RESULTS,
        )
    except Exception as exc:
        logger.exception(f"Channel latest crawl failed for {channel.title}")
        return {"source_status": "api_error", "message": str(exc), "items": []}

    items = []
    for item in api_result.get("items", []):
        snippet = item.get("snippet", {})
        video_id = snippet.get("resourceId", {}).get("videoId", "")
        if not video_id:
            continue
        items.append({
            "youtube_id": video_id,
            "title": snippet.get("title", ""),
            "published_at": snippet.get("publishedAt"),
            "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url"),
        })

    return {
        "source_status": "youtube_api",
        "message": f"Fetched latest videos for {channel.title}.",
        "items": items,
    }


async def _execute_channel_stats(task: CrawlerTask, session: AsyncSession) -> dict[str, Any]:
    channel = await _resolve_channel(task.target, session)
    if not channel:
        return {"source_status": "not_found", "message": "No matching local channel found.", "items": []}

    return {
        "source_status": "local_db",
        "message": f"Loaded local stats for {channel.title}.",
        "items": [{
            "youtube_id": channel.youtube_id,
            "title": channel.title,
            "subscriber_count": channel.subscriber_count,
            "video_count": channel.video_count,
            "view_count": channel.view_count,
            "updated_at": channel.updated_at.isoformat() if channel.updated_at else None,
        }],
    }


async def _execute_keyword_search(task: CrawlerTask) -> dict[str, Any]:
    if not settings.YOUTUBE_API_KEY:
        return {"source_status": "skipped", "message": "YOUTUBE_API_KEY is not configured.", "items": []}
    try:
        from apps.api.services.youtube_api import DualTrackExtractor

        extractor = DualTrackExtractor(api_key=settings.YOUTUBE_API_KEY)
        api_result = await extractor._api.search_list(
            task.target,
            max_results=settings.CRAWLER_DEFAULT_MAX_RESULTS,
        )
    except Exception as exc:
        logger.exception(f"Keyword search crawl failed for '{task.target}'")
        return {"source_status": "api_error", "message": str(exc), "items": []}

    items = []
    for item in api_result.get("items", []):
        snippet = item.get("snippet", {})
        video_id = item.get("id", {}).get("videoId") or item.get("id", {}).get("channelId")
        items.append({
            "youtube_id": video_id,
            "title": snippet.get("title", ""),
            "channel_title": snippet.get("channelTitle", ""),
            "published_at": snippet.get("publishedAt"),
        })
    return {"source_status": "youtube_api", "message": f"Search completed for {task.target}.", "items": items}


async def _resolve_channel(target: str, session: AsyncSession) -> Channel | None:
    if target.isdigit():
        result = await session.execute(select(Channel).where(Channel.id == int(target)))
        return result.scalar_one_or_none()

    result = await session.execute(select(Channel).where(Channel.youtube_id == target))
    channel = result.scalar_one_or_none()
    if channel:
        return channel

    result = await session.execute(select(Channel).where(Channel.title.ilike(f"%{target}%")))
    return result.scalar_one_or_none()
