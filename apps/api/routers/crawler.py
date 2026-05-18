from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.config import settings
from apps.api.schemas import CrawlerTaskCreate, CrawlerTaskRead, CrawlerTaskRunRead
from apps.api.services.crawler_executor import execute_crawler_task
from packages.db.schema import (
    Channel,
    CrawlerRunStatus,
    CrawlerTask,
    CrawlerTaskRun,
    get_db_session,
    get_sessionmaker,
)

router = APIRouter(prefix="/crawler", tags=["Crawler"])
logger = logging.getLogger(__name__)


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
    # CRG: Auto-compute next_run_at for scheduled tasks on creation.
    from apps.api.services.crawler_executor import _calculate_next_run
    if task.frequency != "manual":
        task.next_run_at = _calculate_next_run(task.frequency, datetime.now(timezone.utc))

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


# ── 后台任务执行 ──

async def _run_crawler_background(task_id: int, run_id: int) -> None:
    """在后台执行爬虫任务并更新运行记录."""
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        task = await session.get(CrawlerTask, task_id)
        run = await session.get(CrawlerTaskRun, run_id)
        if not task or not run:
            logger.warning(f"Background task missing refs: task={task_id}, run={run_id}")
            return

        try:
            payload = await execute_crawler_task(task, session, run_id=run_id)
            run.status = CrawlerRunStatus.SUCCESS
            run.source_status = payload["source_status"]
            run.message = payload["message"]
            run.items_found = len(payload.get("items", []))
            run.result_json = json.dumps(payload, ensure_ascii=False)
        except Exception as exc:
            logger.exception(f"Background crawler task {task.id} failed")
            run.status = CrawlerRunStatus.ERROR
            run.source_status = "error"
            run.message = str(exc)
            run.items_found = 0
            run.result_json = json.dumps({"error": str(exc)}, ensure_ascii=False)
        finally:
            now = datetime.now(timezone.utc)
            run.finished_at = now
            task.last_run_at = now
            from apps.api.services.crawler_executor import _calculate_next_run
            if task.frequency != "manual":
                task.next_run_at = _calculate_next_run(task.frequency, now)

        await session.commit()


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
    await session.refresh(run)

    # 后台异步执行，立即返回 run 记录（前端轮询获取进度）
    asyncio.create_task(_run_crawler_background(task.id, run.id))

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


# ── Discovery 发现结果查询 ──

@router.get("/discovery/results", response_model=list[dict[str, Any]])
async def list_discovery_results(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    keyword: Annotated[str | None, Query()] = None,
    min_score: Annotated[float | None, Query(ge=0, le=100)] = None,
    max_age_months: Annotated[int | None, Query(ge=0)] = None,
    max_videos: Annotated[int | None, Query(ge=0)] = None,
    sort_by: Annotated[str, Query(pattern="^(score|views|subscribers|recent)$")] = "score",
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[dict[str, Any]]:
    """查询频道发现结果，支持多维度筛选和排序."""
    query = select(Channel).where(Channel.discovery_score.isnot(None))

    if keyword:
        query = query.where(Channel.discovery_keyword.ilike(f"%{keyword}%"))
    if min_score is not None:
        query = query.where(Channel.discovery_score >= min_score)
    if max_videos is not None:
        query = query.where(Channel.video_count <= max_videos)
    if max_age_months is not None:
        # 粗略过滤：channel_created_at >= now - max_age_months
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_months * 30)
        query = query.where(
            (Channel.channel_created_at.is_(None)) | (Channel.channel_created_at >= cutoff)
        )

    # 排序
    sort_map = {
        "score": desc(Channel.discovery_score),
        "views": desc(Channel.view_count),
        "subscribers": desc(Channel.subscriber_count),
        "recent": desc(Channel.discovered_at),
    }
    query = query.order_by(sort_map.get(sort_by, desc(Channel.discovery_score)))
    query = query.limit(limit)

    result = await session.execute(query)
    channels = result.scalars().all()

    items = []
    for ch in channels:
        age_months = None
        if ch.channel_created_at:
            created = ch.channel_created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            age_days = (datetime.now(timezone.utc) - created).days
            age_months = round(age_days / 30.0, 1)

        items.append({
            "id": ch.id,
            "youtube_id": ch.youtube_id,
            "title": ch.title,
            "thumbnail_url": ch.thumbnail_url,
            "subscriber_count": ch.subscriber_count,
            "video_count": ch.video_count,
            "view_count": ch.view_count,
            "avg_views_per_video": ch.avg_views_per_video,
            "discovery_score": round(ch.discovery_score, 2) if ch.discovery_score else None,
            "discovery_keyword": ch.discovery_keyword,
            "channel_age_months": age_months,
            "discovered_at": ch.discovered_at.isoformat() if ch.discovered_at else None,
        })
    return items


@router.get("/discovery/stats", response_model=dict[str, Any])
async def get_discovery_stats(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    """发现系统统计摘要."""
    # 总发现数
    total_result = await session.execute(
        select(func.count()).select_from(Channel).where(Channel.discovery_score.isnot(None))
    )
    total_discovered = total_result.scalar() or 0

    # 平均评分
    avg_result = await session.execute(
        select(func.avg(Channel.discovery_score)).where(Channel.discovery_score.isnot(None))
    )
    avg_score = round(avg_result.scalar() or 0, 2)

    # 高潜频道数 (>70分)
    high_potential_result = await session.execute(
        select(func.count()).select_from(Channel).where(Channel.discovery_score >= 70)
    )
    high_potential = high_potential_result.scalar() or 0

    # 热门发现关键词 TOP 5
    keyword_result = await session.execute(
        select(
            Channel.discovery_keyword,
            func.count().label("cnt"),
        )
        .where(Channel.discovery_keyword.isnot(None))
        .group_by(Channel.discovery_keyword)
        .order_by(desc("cnt"))
        .limit(5)
    )
    top_keywords = [
        {"keyword": kw, "count": cnt}
        for kw, cnt in keyword_result.all()
    ]

    # 频道年龄分布
    age_buckets = {"<1m": 0, "1-3m": 0, "3-6m": 0, "6-12m": 0, ">12m": 0}
    channels_result = await session.execute(
        select(Channel.channel_created_at).where(Channel.channel_created_at.isnot(None))
    )
    now = datetime.now(timezone.utc)
    for (created_at,) in channels_result.all():
        if created_at is None:
            continue
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        age_days = (now - created_at).days
        if age_days < 30:
            age_buckets["<1m"] += 1
        elif age_days < 90:
            age_buckets["1-3m"] += 1
        elif age_days < 180:
            age_buckets["3-6m"] += 1
        elif age_days < 365:
            age_buckets["6-12m"] += 1
        else:
            age_buckets[">12m"] += 1

    return {
        "total_discovered_channels": total_discovered,
        "avg_score": avg_score,
        "high_potential_count": high_potential,
        "top_keywords": top_keywords,
        "channels_by_age_range": age_buckets,
    }


@router.get("/analytics", response_model=dict[str, Any])
async def get_crawler_analytics(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    days: Annotated[int, Query(ge=1, le=90)] = 14,
) -> dict[str, Any]:
    """爬虫系统综合分析面板数据."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # ── 任务统计 ──
    task_count_result = await session.execute(select(func.count()).select_from(CrawlerTask))
    task_count = task_count_result.scalar() or 0

    # ── 运行统计 ──
    total_runs_result = await session.execute(
        select(func.count()).select_from(CrawlerTaskRun).where(CrawlerTaskRun.started_at >= cutoff)
    )
    total_runs = total_runs_result.scalar() or 0

    success_runs_result = await session.execute(
        select(func.count())
        .select_from(CrawlerTaskRun)
        .where(CrawlerTaskRun.started_at >= cutoff, CrawlerTaskRun.status == CrawlerRunStatus.SUCCESS)
    )
    success_runs = success_runs_result.scalar() or 0
    success_rate = round(success_runs / total_runs, 2) if total_runs > 0 else 0.0

    # ── 运行趋势（按天聚合）──
    run_rows_result = await session.execute(
        select(CrawlerTaskRun.started_at, CrawlerTaskRun.status)
        .where(CrawlerTaskRun.started_at >= cutoff)
        .order_by(CrawlerTaskRun.started_at)
    )
    run_trend_map: dict[str, dict[str, int]] = {}
    for (started_at, status) in run_rows_result.all():
        if started_at is None:
            continue
        d = started_at.strftime("%Y-%m-%d")
        bucket = run_trend_map.setdefault(d, {"success": 0, "error": 0})
        bucket["success" if status == CrawlerRunStatus.SUCCESS else "error"] += 1
    run_trend = [{"date": d, **v} for d, v in sorted(run_trend_map.items())]

    # ── 发现趋势（按天聚合新频道）──
    disc_rows_result = await session.execute(
        select(Channel.discovered_at)
        .where(Channel.discovered_at >= cutoff, Channel.discovery_score.isnot(None))
        .order_by(Channel.discovered_at)
    )
    disc_trend_map: dict[str, int] = {}
    for (discovered_at,) in disc_rows_result.all():
        if discovered_at is None:
            continue
        d = discovered_at.strftime("%Y-%m-%d")
        disc_trend_map[d] = disc_trend_map.get(d, 0) + 1
    discovery_trend = [{"date": d, "count": c} for d, c in sorted(disc_trend_map.items())]

    # ── 发现统计 ──
    total_discovered_result = await session.execute(
        select(func.count()).select_from(Channel).where(Channel.discovery_score.isnot(None))
    )
    total_discovered = total_discovered_result.scalar() or 0

    avg_score_result = await session.execute(
        select(func.avg(Channel.discovery_score)).where(Channel.discovery_score.isnot(None))
    )
    avg_score = round(avg_score_result.scalar() or 0, 2)

    high_potential_result = await session.execute(
        select(func.count()).select_from(Channel).where(Channel.discovery_score >= 70)
    )
    high_potential = high_potential_result.scalar() or 0

    # ── 评分分布 ──
    score_ranges = {"<50": 0, "50-60": 0, "60-70": 0, "70-80": 0, "80+": 0}
    score_rows = await session.execute(
        select(Channel.discovery_score).where(Channel.discovery_score.isnot(None))
    )
    for (score,) in score_rows.all():
        if score is None:
            continue
        if score < 50:
            score_ranges["<50"] += 1
        elif score < 60:
            score_ranges["50-60"] += 1
        elif score < 70:
            score_ranges["60-70"] += 1
        elif score < 80:
            score_ranges["70-80"] += 1
        else:
            score_ranges["80+"] += 1

    # ── 热门关键词 TOP 10 ──
    keyword_result = await session.execute(
        select(
            Channel.discovery_keyword,
            func.count().label("cnt"),
            func.avg(Channel.discovery_score).label("avg_score"),
        )
        .where(Channel.discovery_keyword.isnot(None))
        .group_by(Channel.discovery_keyword)
        .order_by(desc("cnt"))
        .limit(10)
    )
    top_keywords = [
        {"keyword": kw, "count": cnt, "avg_score": round(avg_s or 0, 1)}
        for kw, cnt, avg_s in keyword_result.all()
    ]

    return {
        "days": days,
        "task_count": task_count,
        "total_runs": total_runs,
        "success_runs": success_runs,
        "success_rate": success_rate,
        "total_discovered": total_discovered,
        "avg_score": avg_score,
        "high_potential_count": high_potential,
        "run_trend": run_trend,
        "discovery_trend": discovery_trend,
        "score_distribution": score_ranges,
        "top_keywords": top_keywords,
    }
