"""
后台定时调度服务 — 自动监控 + 数据更新

功能:
  - 定期更新所有频道统计 (subscriber/view/video_count)
  - 自动检测新视频并入库
  - 写入 metric_history 时间序列
  - 监控任务状态管理

调度策略:
  - 频道统计更新: 每 6 小时
  - 新视频检测: 每 4 小时
  - metric_history 快照: 每 12 小时
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select


from apps.api.config import settings
from apps.api.services.crawler_executor import run_due_crawler_tasks
from packages.db.schema import Channel, MetricHistory, MetricType, Video, get_sessionmaker

logger = logging.getLogger("scheduler")

# 全局调度器实例
_scheduler: AsyncIOScheduler | None = None


def _uploads_playlist_id(youtube_id: str) -> str | None:
    # CRG: Keep UC-channel playlist derivation in one place for scheduler and tests.
    return f"UU{youtube_id[2:]}" if youtube_id.startswith("UC") else None


def _upload_item_from_ytdlp_meta(meta: Any) -> dict[str, Any]:
    # CRG: Normalize yt-dlp fallback output to the same shape as playlistItems.
    return {
        "snippet": {
            "resourceId": {"videoId": meta.video_id},
            "title": meta.title,
            "thumbnails": {"high": {"url": meta.thumbnail_url or ""}},
        }
    }


def _video_payload_from_upload_item(item: dict[str, Any]) -> dict[str, Any] | None:
    snippet = item.get("snippet", {})
    video_id = snippet.get("resourceId", {}).get("videoId", "")
    if not video_id:
        return None
    # CRG: Keep upload-item parsing reusable before duplicate checks create Video rows.
    return {
        "youtube_id": video_id,
        "title": snippet.get("title", "Unknown"),
        "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url"),
    }


def get_scheduler() -> AsyncIOScheduler:
    """获取或创建调度器实例."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone="UTC")
    return _scheduler


async def update_all_channel_stats() -> None:
    """更新所有频道的最新统计数据."""
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        try:
            result = await session.execute(select(Channel))
            channels = result.scalars().all()
            if not channels:
                logger.info("No channels to update")
                return

            from apps.api.services.youtube_api import DualTrackExtractor
            extractor = DualTrackExtractor(api_key=settings.YOUTUBE_API_KEY)

            # CRG: Batch API calls (50 IDs/call) to avoid N+1 API storm.
            BATCH_SIZE = 50
            updated = 0
            for i in range(0, len(channels), BATCH_SIZE):
                batch = channels[i:i + BATCH_SIZE]
                try:
                    detail = await extractor.get_channel_details([c.youtube_id for c in batch])
                    items = detail.get("items", [])
                    stats_map = {item["id"]: item.get("statistics", {}) for item in items}

                    for channel in batch:
                        stats = stats_map.get(channel.youtube_id, {})
                        if not stats:
                            continue
                        subscriber_count = int(stats["subscriberCount"]) if stats.get("subscriberCount") else None
                        video_count = int(stats["videoCount"]) if stats.get("videoCount") else None
                        view_count = int(stats["viewCount"]) if stats.get("viewCount") else None

                        channel.subscriber_count = subscriber_count
                        channel.video_count = video_count
                        channel.view_count = view_count
                        channel.updated_at = datetime.now(timezone.utc)
                        updated += 1
                except Exception as e:
                    logger.warning(f"Failed to update batch starting with {batch[0].youtube_id}: {e}")

            await session.commit()
            logger.info(f"Updated {updated}/{len(channels)} channels")
        except Exception as e:
            await session.rollback()
            logger.exception(f"Channel stats update failed: {e}")
            raise


async def detect_new_videos() -> None:
    """检测所有监控频道的新视频并入库 (走 DualTrackExtractor)."""
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        try:
            jobs = await _load_active_monitor_jobs(session)
            if not jobs:
                logger.info("No active monitor jobs")
                return

            from apps.api.services.youtube_api import DualTrackExtractor
            extractor = DualTrackExtractor(api_key=settings.YOUTUBE_API_KEY)

            imported = 0
            for job, channel in jobs:
                try:
                    items = await _fetch_latest_upload_items(extractor, channel)
                    imported += await _insert_new_videos(session, channel, items)
                    job.last_run_at = datetime.now(timezone.utc)
                    # CRG: The scheduled job now delegates fetch and insert details to focused helpers.
                except Exception as e:
                    logger.warning(f"Failed to detect new videos for {channel.title}: {e}")

            await session.commit()
            logger.info(f"Imported {imported} new videos")
        except Exception as e:
            await session.rollback()
            logger.error(f"New video detection failed: {e}")


async def _load_active_monitor_jobs(session: Any) -> list[Any]:
    from packages.db.schema import MonitorJob
    result = await session.execute(
        select(MonitorJob, Channel)
        .join(Channel, MonitorJob.channel_id == Channel.id)
        .where(MonitorJob.status == "active")
    )
    # CRG: Keep monitor-job query separate from external fetch and insert logic.
    return list(result.all())


async def _fetch_latest_upload_items(extractor: Any, channel: Channel) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    has_quota = await extractor._quota.check_budget(needed=1)
    playlist_id = _uploads_playlist_id(channel.youtube_id)
    if has_quota and extractor._api._is_available() and playlist_id:
        api_result = await extractor._api.playlist_items_list(playlist_id, max_results=10)
        items = api_result.get("items", [])
    if items:
        return items

    ytdlp_result = await extractor._yt_dlp.extract_channel_uploads(
        f"https://www.youtube.com/channel/{channel.youtube_id}", max_videos=10
    )
    # CRG: yt-dlp fallback feeds the same downstream item parser as YouTube API results.
    return [_upload_item_from_ytdlp_meta(meta) for meta in ytdlp_result]


async def _insert_new_videos(session: Any, channel: Channel, items: list[dict[str, Any]]) -> int:
    imported = 0
    for item in items:
        payload = _video_payload_from_upload_item(item)
        if not payload:
            continue
        existing = await session.execute(select(Video).where(Video.youtube_id == payload["youtube_id"]))
        if existing.scalar_one_or_none():
            continue
        session.add(Video(channel_id=channel.id, published_at=None, **payload))
        imported += 1
    return imported


async def scrape_video_comments() -> None:
    """抓取高观看视频的评论并保存到 analysis_logs."""
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        try:
            from packages.db.schema import AnalysisLog, AnalysisType
            from apps.api.services.youtube_api import DualTrackExtractor
            extractor = DualTrackExtractor(api_key=settings.YOUTUBE_API_KEY)

            # 找观看数最高的 10 个尚未分析评论的视频
            result = await session.execute(
                select(Video).where(Video.view_count > 100000)
                .order_by(Video.view_count.desc())
                .limit(10)
            )
            videos = result.scalars().all()
            if not videos:
                logger.info("No high-view videos to scrape comments")
                return

            scraped = 0
            for video in videos:
                try:
                    comments = await extractor.get_comments(video.youtube_id, max_results=20)
                    if not comments:
                        continue

                    # 保存到 analysis_logs (sentiment 类型)
                    from apps.api.services.analyzer import CommentSentimentAnalyzer
                    analyzer = CommentSentimentAnalyzer()
                    agg = analyzer.aggregate(analyzer.batch_analyze(comments))
                    score = agg.get("avg_compound", 0) * 50 + 50

                    log = AnalysisLog(
                        video_id=video.id,
                        analysis_type=AnalysisType.SENTIMENT,
                        result_json=str({"comment_count": len(comments), "aggregation": agg}),
                        score=score,
                    )
                    session.add(log)
                    scraped += 1
                except Exception as e:
                    logger.warning(f"Failed to scrape comments for {video.youtube_id}: {e}")

            await session.commit()
            logger.info(f"Scraped comments for {scraped}/{len(videos)} videos")
        except Exception as e:
            await session.rollback()
            logger.error(f"Comment scraping failed: {e}")


async def snapshot_metrics() -> None:
    """为所有频道写入指标历史快照."""
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        try:
            result = await session.execute(select(Channel))
            channels = result.scalars().all()
            if not channels:
                return

            now = datetime.now(timezone.utc)
            for channel in channels:
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

            await session.commit()
            logger.info(f"Snapshotted metrics for {len(channels)} channels")
        except Exception as e:
            await session.rollback()
            logger.error(f"Metric snapshot failed: {e}")


def init_scheduler() -> AsyncIOScheduler:
    """初始化并启动调度器."""
    scheduler = get_scheduler()

    # 频道统计更新: 每 6 小时
    scheduler.add_job(
        update_all_channel_stats,
        trigger=IntervalTrigger(hours=6),
        id="update_channel_stats",
        name="Update channel statistics",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=300,
    )

    # 新视频检测: 每 4 小时
    scheduler.add_job(
        detect_new_videos,
        trigger=IntervalTrigger(hours=4),
        id="detect_new_videos",
        name="Detect new videos",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=300,
    )

    # 指标快照: 每 12 小时
    scheduler.add_job(
        snapshot_metrics,
        trigger=IntervalTrigger(hours=12),
        id="snapshot_metrics",
        name="Snapshot metrics history",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=300,
    )

    # 评论抓取: 每 8 小时
    scheduler.add_job(
        scrape_video_comments,
        trigger=IntervalTrigger(hours=8),
        id="scrape_comments",
        name="Scrape video comments",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=300,
    )

    # CrawlerTask 自动轮询: 每 10 分钟检查一次到期任务
    scheduler.add_job(
        run_due_crawler_tasks,
        trigger=IntervalTrigger(minutes=10),
        id="run_due_crawler_tasks",
        name="Run due crawler tasks",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=300,
    )

    scheduler.start()
    logger.info("Scheduler started with 5 jobs: stats(6h), videos(4h), metrics(12h), comments(8h), crawler_tasks(10m)")
    return scheduler


def shutdown_scheduler() -> None:
    """关闭调度器."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler shut down")
