"""
CrawlerTask 执行引擎 —— 供路由和调度器共享使用

功能:
  - 根据 task_type 分发到具体执行逻辑
  - channel_latest: 抓取频道最新视频
  - channel_stats: 抓取频道统计
  - keyword_search: 关键词搜索 + 自动入库频道和视频
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any

import httplib2
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.config import settings
from apps.api.services.channel_service import build_channel_values, get_channel_by_youtube_id
from apps.api.services.video_service import build_video_from_youtube_item, import_videos_from_items
from apps.api.services.youtube_api import DualTrackExtractor
from packages.db.schema import Channel, ChannelDiscoveryResult, ContentProject, CrawlerRunStatus, CrawlerTask, CrawlerTaskRun, Video, get_sessionmaker

logger = logging.getLogger("crawler_executor")

# 共享 ThreadPoolExecutor 用于 yt-dlp 降级（避免每次创建新线程池导致泄漏）
_ytdlp_executor = None

def _get_ytdlp_executor():
    global _ytdlp_executor
    if _ytdlp_executor is None:
        from concurrent.futures import ThreadPoolExecutor
        _ytdlp_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="ytdlp")
    return _ytdlp_executor


# 共享 httplib2.Http 客户端用于网页抓取（零配额搜索）
_http_client = None

def _get_http_client() -> httplib2.Http:
    global _http_client
    if _http_client is None:
        proxy_url = settings.PROXY_URL or ""
        if proxy_url:
            proxy_host = proxy_url.replace("http://", "").replace("https://", "").rsplit(":", 1)[0]
            proxy_port = int(proxy_url.rsplit(":", 1)[-1])
            _http_client = httplib2.Http(
                timeout=15,
                proxy_info=httplib2.ProxyInfo(
                    proxy_type=httplib2.socks.PROXY_TYPE_HTTP,
                    proxy_host=proxy_host,
                    proxy_port=proxy_port,
                )
            )
        else:
            _http_client = httplib2.Http(timeout=15)
    return _http_client

# ── 频率映射到 timedelta ──
_FREQ_DELTA: dict[str, timedelta] = {
    "hourly": timedelta(hours=1),
    "daily": timedelta(days=1),
    "weekly": timedelta(weeks=1),
}


# =============================================================================
# 公共入口
# =============================================================================

async def execute_crawler_task(task: CrawlerTask, session: AsyncSession, run_id: int | None = None) -> dict[str, Any]:
    """执行单个 CrawlerTask 并返回结果 payload."""
    if task.task_type == "channel_latest":
        return await _execute_channel_latest(task, session)
    if task.task_type == "channel_stats":
        return await _execute_channel_stats(task, session)
    if task.task_type == "keyword_search":
        return await _execute_keyword_search(task, session)
    if task.task_type == "channel_discovery":
        return await _execute_channel_discovery(task, session, run_id=run_id)
    return {"source_status": "skipped", "message": f"Unsupported task type: {task.task_type}", "items": []}


async def run_due_crawler_tasks() -> None:
    """调度器轮询入口 —— 执行所有到期的 CrawlerTask."""
    from packages.db.schema import get_sessionmaker

    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        now = datetime.now(timezone.utc)
        # 查询活跃且非手动的任务
        result = await session.execute(
            select(CrawlerTask).where(
                CrawlerTask.status == "active",
                CrawlerTask.frequency != "manual",
            )
        )
        tasks = result.scalars().all()
        if not tasks:
            logger.debug("No active scheduled crawler tasks")
            return

        executed = 0
        for task in tasks:
            # 判断任务是否到期
            if not _is_task_due(task, now):
                continue

            # 创建运行记录
            run = CrawlerTaskRun(task_id=task.id, status=CrawlerRunStatus.RUNNING)
            session.add(run)
            await session.flush()

            try:
                payload = await execute_crawler_task(task, session, run_id=run.id)
                run.status = CrawlerRunStatus.SUCCESS
                run.source_status = payload["source_status"]
                run.message = payload["message"]
                run.items_found = payload.get("channels_imported", 0) + payload.get("videos_imported", 0)
                run.result_json = json.dumps(payload, ensure_ascii=False)
            except Exception as exc:
                logger.exception(f"Scheduled crawler task {task.id} ({task.name}) failed")
                run.status = CrawlerRunStatus.ERROR
                run.source_status = "error"
                run.message = str(exc)
                run.items_found = 0
                run.result_json = json.dumps({"error": str(exc)}, ensure_ascii=False)

                # ── 自动重试：退避策略 ──
                try:
                    # 查询最近 5 次运行（排除当前正在创建的这条）
                    from sqlalchemy import select
                    recent_runs_result = await session.execute(
                        select(CrawlerTaskRun).where(CrawlerTaskRun.task_id == task.id).order_by(CrawlerTaskRun.started_at.desc()).limit(5)
                    )
                    recent_runs = recent_runs_result.scalars().all()
                    fail_count = sum(1 for r in recent_runs if r.status == CrawlerRunStatus.ERROR)
                    backoff_minutes = {1: 10, 2: 30, 3: 60}.get(fail_count, 180)
                    retry_at = datetime.now(timezone.utc) + timedelta(minutes=backoff_minutes)
                    logger.warning(f"Task {task.id} will retry in {backoff_minutes}min (consecutive_failures={fail_count})")
                except Exception:
                    retry_at = datetime.now(timezone.utc) + timedelta(minutes=10)
            finally:
                finished = datetime.now(timezone.utc)
                run.finished_at = finished
                task.last_run_at = finished
                if run.status == CrawlerRunStatus.ERROR:
                    task.next_run_at = retry_at
                else:
                    task.next_run_at = _calculate_next_run(task.frequency, finished)
                executed += 1

        await session.commit()
        if executed:
            logger.info(f"Executed {executed}/{len(tasks)} due crawler tasks")


# =============================================================================
# 内部 helpers
# =============================================================================

def _is_task_due(task: CrawlerTask, now: datetime) -> bool:
    """判断任务是否到达执行时间."""
    # 如果 next_run_at 已设置，直接比较
    if task.next_run_at is not None:
        return task.next_run_at <= now
    # 否则根据 last_run_at + frequency 计算
    if task.last_run_at is None:
        return True  # 从未执行过，立即执行
    delta = _FREQ_DELTA.get(task.frequency)
    if delta is None:
        return False
    return task.last_run_at + delta <= now


def _calculate_next_run(frequency: str, base: datetime) -> datetime | None:
    """根据频率计算下次执行时间."""
    delta = _FREQ_DELTA.get(frequency)
    return base + delta if delta else None


async def _resolve_channel(target: str, session: AsyncSession) -> Channel | None:
    """从 target 字符串解析出 Channel."""
    if target.isdigit():
        result = await session.execute(select(Channel).where(Channel.id == int(target)))
        return result.scalar_one_or_none()

    result = await session.execute(select(Channel).where(Channel.youtube_id == target))
    channel = result.scalar_one_or_none()
    if channel:
        return channel

    result = await session.execute(
        select(Channel).where(Channel.title.ilike(f"%{target}%")).limit(1)
    )
    return result.scalars().first()


# =============================================================================
# 任务类型执行器
# =============================================================================

async def _execute_channel_latest(task: CrawlerTask, session: AsyncSession) -> dict[str, Any]:
    channel = await _resolve_channel(task.target, session)

    # 如果本地没有该频道，尝试通过 YouTube API 自动获取并入库
    if not channel:
        # 尝试把 target 当作 YouTube 频道 ID / handle / 自定义 URL 来解析
        target = task.target.strip()
        if not target:
            return {"source_status": "not_found", "message": "Target is empty.", "items": []}

        try:
            extractor = DualTrackExtractor(api_key=settings.YOUTUBE_API_KEY)
            # 先尝试 search 找到频道（支持 @handle、频道名、自定义 URL）
            search_result = await extractor._api.search_list(
                target, max_results=3, search_type="channel"
            )
            search_items = search_result.get("items", [])
            if not search_items:
                return {"source_status": "not_found", "message": f"No channel found for '{target}' on YouTube.", "items": []}

            # 取第一个结果，获取详情
            candidate = search_items[0]
            candidate_id = candidate.get("snippet", {}).get("channelId") or candidate.get("id", {}).get("channelId")
            if not candidate_id:
                return {"source_status": "not_found", "message": f"Could not resolve channel ID for '{target}'.", "items": []}

            detail_result = await extractor.get_channel_details([candidate_id])
            detail_items = detail_result.get("items", [])
            if not detail_items:
                return {"source_status": "not_found", "message": f"Could not fetch channel details for '{target}'.", "items": []}

            detail_item = detail_items[0]
            from apps.api.services.channel_service import build_channel_values
            channel = Channel(**build_channel_values(candidate_id, candidate.get("snippet", {}), detail_item))
            session.add(channel)
            await session.flush()
            logger.info(f"Auto-imported channel for crawler task: {channel.title} ({candidate_id})")
        except Exception as exc:
            logger.warning(f"Failed to auto-import channel for target '{target}': {exc}")
            return {"source_status": "not_found", "message": f"Channel '{target}' not found locally and auto-import failed: {exc}", "items": []}

    # CRG: Validate YouTube channel ID format before calling API.
    if not channel.youtube_id or not channel.youtube_id.startswith("UC") or len(channel.youtube_id) < 5:
        return {
            "source_status": "skipped",
            "message": f"Invalid YouTube channel ID: '{channel.youtube_id}'. Must start with 'UC'.",
            "items": [],
        }

    uploads_playlist_id = f"UU{channel.youtube_id[2:]}"
    if not uploads_playlist_id:
        return {"source_status": "skipped", "message": "Target is not a UC channel id.", "items": []}

    items: list[dict[str, Any]] = []
    api_ok = False

    # ── 尝试 1: YouTube Data API ──
    if settings.YOUTUBE_API_KEY:
        try:
            extractor = DualTrackExtractor(api_key=settings.YOUTUBE_API_KEY)
            api_result = await extractor._api.playlist_items_list(
                uploads_playlist_id,
                max_results=settings.CRAWLER_DEFAULT_MAX_RESULTS,
            )
            if "error" not in api_result:
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
                api_ok = True
                logger.info(f"Channel latest for '{channel.title}' via API: {len(items)} items")
        except Exception as exc:
            logger.warning(f"API playlist_items failed for '{channel.title}', will try yt-dlp: {exc}")

    # ── 尝试 2: yt-dlp 降级 ──
    if not api_ok:
        try:
            logger.info(f"Channel latest for '{channel.title}' via yt-dlp fallback")
            ytdlp_items = await _fetch_channel_uploads_ytdlp(
                channel.youtube_id,
                max_results=settings.CRAWLER_DEFAULT_MAX_RESULTS,
            )
            items = ytdlp_items
        except Exception as exc:
            logger.exception(f"yt-dlp fallback also failed for '{channel.title}'")
            diag = (
                f"YouTube 无法访问。可能原因："
                f"1) VPN 未开启或仅浏览器代理模式；"
                f"2) 代理端口不匹配（当前配置: {settings.PROXY_URL or '自动探测'}）；"
                f"3) VPN 为 TUN 模式但 PROXY_AUTO_DETECT 被禁用。"
                f"原始错误: {exc}"
            )
            return {"source_status": "api_error", "message": diag, "items": []}

    return {
        "source_status": "youtube_api" if api_ok else "yt_dlp",
        "message": f"Fetched latest videos for {channel.title}.",
        "items": items,
    }


async def _execute_channel_stats(task: CrawlerTask, session: AsyncSession) -> dict[str, Any]:
    channel = await _resolve_channel(task.target, session)

    # 本地没有时尝试自动导入（复用 channel_latest 的导入逻辑）
    if not channel:
        target = task.target.strip()
        try:
            extractor = DualTrackExtractor(api_key=settings.YOUTUBE_API_KEY)
            search_result = await extractor._api.search_list(
                target, max_results=3, search_type="channel"
            )
            search_items = search_result.get("items", [])
            if not search_items:
                return {"source_status": "not_found", "message": f"No channel found for '{target}'.", "items": []}

            candidate = search_items[0]
            candidate_id = candidate.get("snippet", {}).get("channelId") or candidate.get("id", {}).get("channelId")
            if not candidate_id:
                return {"source_status": "not_found", "message": f"Could not resolve channel ID for '{target}'.", "items": []}

            detail_result = await extractor.get_channel_details([candidate_id])
            detail_items = detail_result.get("items", [])
            if not detail_items:
                return {"source_status": "not_found", "message": f"Could not fetch details for '{target}'.", "items": []}

            from apps.api.services.channel_service import build_channel_values
            channel = Channel(**build_channel_values(candidate_id, candidate.get("snippet", {}), detail_items[0]))
            session.add(channel)
            await session.flush()
            logger.info(f"Auto-imported channel for stats task: {channel.title} ({candidate_id})")
        except Exception as exc:
            return {"source_status": "not_found", "message": f"Channel '{target}' not found and auto-import failed: {exc}", "items": []}

    # 同时更新数据库中的 stats
    try:
        extractor = DualTrackExtractor(api_key=settings.YOUTUBE_API_KEY)
        detail = await extractor.get_channel_details([channel.youtube_id])
        stats = detail.get("items", [{}])[0].get("statistics", {})
        if stats:
            channel.subscriber_count = int(stats["subscriberCount"]) if stats.get("subscriberCount") else None
            channel.video_count = int(stats["videoCount"]) if stats.get("videoCount") else None
            channel.view_count = int(stats["viewCount"]) if stats.get("viewCount") else None
            channel.updated_at = datetime.now(timezone.utc)
    except Exception as exc:
        logger.warning(f"Failed to refresh stats for {channel.title}: {exc}")

    return {
        "source_status": "local_db",
        "message": f"Loaded stats for {channel.title}.",
        "items": [{
            "youtube_id": channel.youtube_id,
            "title": channel.title,
            "subscriber_count": channel.subscriber_count,
            "video_count": channel.video_count,
            "view_count": channel.view_count,
            "updated_at": channel.updated_at.isoformat() if channel.updated_at else None,
        }],
    }


async def _execute_keyword_search(task: CrawlerTask, session: AsyncSession) -> dict[str, Any]:
    """关键词搜索 + 自动入库频道和视频.

    策略:
      1. 优先使用 YouTube Data API (search.list)
      2. API 连接失败/超时时降级到 yt-dlp 搜索
      3. 搜索结果中的频道和视频自动入库
    """
    extractor = DualTrackExtractor(api_key=settings.YOUTUBE_API_KEY)
    search_items: list[dict[str, Any]] = []

    # ── 尝试 1: YouTube Data API ──
    api_ok = False
    if settings.YOUTUBE_API_KEY:
        try:
            api_result = await extractor._api.search_list(
                task.target,
                max_results=settings.CRAWLER_DEFAULT_MAX_RESULTS,
                search_type="video",
            )
            if "error" not in api_result:
                search_items = api_result.get("items", [])
                api_ok = True
                logger.info(f"Keyword search '{task.target}' via API: {len(search_items)} results")
        except Exception as exc:
            logger.warning(f"API search failed for '{task.target}', falling back to yt-dlp: {exc}")

    # ── 尝试 2: yt-dlp 降级 ──
    if not api_ok or not search_items:
        try:
            logger.info(f"Keyword search '{task.target}' via yt-dlp fallback")
            ytdlp_items = await _search_ytdlp(task.target, max_results=settings.CRAWLER_DEFAULT_MAX_RESULTS)
            search_items = ytdlp_items
        except Exception as exc:
            logger.exception(f"yt-dlp search also failed for '{task.target}'")
            diag = (
                f"YouTube 无法访问。可能原因："
                f"1) VPN 未开启或仅浏览器代理模式；"
                f"2) 代理端口不匹配（当前配置: {settings.PROXY_URL or '自动探测'}）；"
                f"3) VPN 为 TUN 模式但 PROXY_AUTO_DETECT 被禁用。"
                f"原始错误: {exc}"
            )
            return {"source_status": "api_error", "message": diag, "items": []}

    if not search_items:
        return {"source_status": "empty", "message": f"No results found for '{task.target}'.", "items": []}
    if not search_items:
        return {"source_status": "empty", "message": f"No results found for '{task.target}'.", "items": []}

    # ── 阶段 1: 提取频道 ID 并去重 ──
    channel_ids: set[str] = set()
    video_ids: list[str] = []
    video_to_channel: dict[str, str] = {}  # video_id -> channel_youtube_id

    for item in search_items:
        snippet = item.get("snippet", {})
        vid = item.get("id", {}).get("videoId")
        cid = snippet.get("channelId")
        if vid and cid:
            video_ids.append(vid)
            channel_ids.add(cid)
            video_to_channel[vid] = cid

    if not channel_ids:
        return {"source_status": "empty", "message": "No valid channels found in search results.", "items": []}

    # ── 阶段 2: 批量获取频道详情并入库 ──
    channels_imported = 0
    channels_skipped = 0
    channel_id_map: dict[str, int] = {}  # youtube_id -> local Channel.id

    # 先检查哪些频道已存在
    for cid in channel_ids:
        existing = await get_channel_by_youtube_id(session, cid)
        if existing:
            channel_id_map[cid] = existing.id
            channels_skipped += 1

    new_channel_ids = [cid for cid in channel_ids if cid not in channel_id_map]
    if new_channel_ids:
        try:
            detail_result = await extractor.get_channel_details(new_channel_ids)
            detail_items = {item["id"]: item for item in detail_result.get("items", []) if item.get("id")}

            for cid in new_channel_ids:
                detail_item = detail_items.get(cid)
                fallback_snippet = {}
                # 从搜索结果中找 fallback snippet
                for item in search_items:
                    if item.get("snippet", {}).get("channelId") == cid:
                        fallback_snippet = item.get("snippet", {})
                        break

                channel = Channel(**build_channel_values(cid, fallback_snippet, detail_item))
                session.add(channel)
                await session.flush()
                channel_id_map[cid] = channel.id
                channels_imported += 1
                logger.info(f"Imported channel: {channel.title} ({cid})")
        except Exception as exc:
            logger.warning(f"Failed to import channels for search '{task.target}': {exc}")

    # ── 阶段 3: 批量获取视频详情并入库 ──
    videos_imported = 0
    videos_skipped = 0

    if video_ids:
        try:
            video_detail_result = await extractor.get_video_details(video_ids)
            video_items = video_detail_result.get("items", [])

            for item in video_items:
                vid = item.get("id", "")
                cid_yt = video_to_channel.get(vid)
                cid_local = channel_id_map.get(cid_yt) if cid_yt else None
                if not cid_local:
                    continue

                existing = await session.execute(select(Video).where(Video.youtube_id == vid))
                if existing.scalar_one_or_none():
                    videos_skipped += 1
                    continue

                video = build_video_from_youtube_item(item, cid_local)
                if video:
                    # fix: published_at from snippet since build_video_from_youtube_item sets None
                    snippet = item.get("snippet", {})
                    published = snippet.get("publishedAt")
                    if published:
                        try:
                            video.published_at = datetime.fromisoformat(published.replace("Z", "+00:00"))
                        except ValueError:
                            pass
                    session.add(video)
                    videos_imported += 1

            await session.flush()
            logger.info(f"Imported {videos_imported} videos for search '{task.target}'")
        except Exception as exc:
            logger.warning(f"Failed to import videos for search '{task.target}': {exc}")

    return {
        "source_status": "youtube_api",
        "message": f"Search '{task.target}' completed. Imported {channels_imported} channels, {videos_imported} videos.",
        "items": [{"youtube_id": vid, "title": "", "channel_title": ""} for vid in video_ids],
        "channels_imported": channels_imported,
        "channels_skipped": channels_skipped,
        "videos_imported": videos_imported,
        "videos_skipped": videos_skipped,
    }


# =============================================================================
# yt-dlp 降级搜索（带代理自动回退）
# =============================================================================

def _build_ytdlp_opts(base_opts: dict[str, Any]) -> dict[str, Any]:
    """构建 yt-dlp 选项，优先使用配置代理，失败时自动回退直连."""
    opts = dict(base_opts)
    opts["socket_timeout"] = 30
    # 智能代理：配置优先，但先检测可用性；不可用则回退直连
    effective_proxy = settings.PROXY_URL
    if effective_proxy:
        from apps.api.services.youtube_api import is_proxy_reachable
        if is_proxy_reachable(effective_proxy):
            opts["proxy"] = effective_proxy
        else:
            logger.warning(f"Proxy unreachable: {effective_proxy}, yt-dlp will use direct connection")
    return opts


def _ytdlp_extract(url: str, base_opts: dict[str, Any]) -> Any:
    """执行 yt-dlp 提取，代理失败时自动回退直连."""
    import yt_dlp
    ydl_opts = _build_ytdlp_opts(base_opts)
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as first_exc:
        # 代理相关错误时回退直连（通过异常类型 + 错误码判断，避免字符串误匹配）
        exc_msg = str(first_exc).lower()
        is_proxy_error = (
            "proxy" in exc_msg
            or "unable to connect to proxy" in exc_msg
            or "connection" in exc_msg
            or "10061" in exc_msg
            or "10060" in exc_msg
            or "network is unreachable" in exc_msg
        )
        if is_proxy_error and "proxy" in ydl_opts:
            logger.warning(f"yt-dlp proxy failed, retrying direct: {first_exc}")
            ydl_opts.pop("proxy", None)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
        raise
    except Exception:
        raise


async def _search_ytdlp(query: str, max_results: int = 25) -> list[dict[str, Any]]:
    """使用 yt-dlp 搜索 YouTube 视频（零配额，无需 API key）.

    支持大数量搜索（max_results 最大约 500，受 YouTube 返回限制）.
    Returns:
        模拟 YouTube API search.list 响应格式的 item 列表.
    """
    import asyncio

    def _extract() -> list[dict[str, Any]]:
        # ytsearch 语法支持较大数字，但 YouTube 实际返回通常 < 500
        search_count = min(max_results, 500)
        search_url = f"ytsearch{search_count}:{query}"
        info = _ytdlp_extract(search_url, {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": False,
            "playlistend": search_count,
        })
        entries = info.get("entries", []) if info else []
        items = []
        for entry in entries:
            if not entry:
                continue
            items.append({
                "id": {"videoId": entry.get("id", "")},
                "snippet": {
                    "title": entry.get("title", ""),
                    "channelId": entry.get("channel_id", ""),
                    "channelTitle": entry.get("channel", ""),
                    "publishedAt": entry.get("upload_date", ""),
                    "thumbnails": {
                        "high": {"url": entry.get("thumbnail", "")}
                    } if entry.get("thumbnail") else {},
                    "description": entry.get("description", ""),
                },
            })
        return items

    loop = asyncio.get_running_loop()
    return await asyncio.wait_for(
        loop.run_in_executor(_get_ytdlp_executor(), _extract),
        timeout=120,  # 大数量搜索需要更长时间
    )


async def _fetch_channel_uploads_ytdlp(channel_id: str, max_results: int = 25) -> list[dict[str, Any]]:
    """使用 yt-dlp 获取频道最新上传视频（API 失败时的降级方案）."""
    import asyncio

    def _extract() -> list[dict[str, Any]]:
        channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"
        info = _ytdlp_extract(channel_url, {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": False,
            "playlistend": max_results,
        })
        entries = info.get("entries", []) if info else []
        items = []
        for entry in entries:
            if not entry:
                continue
            items.append({
                "youtube_id": entry.get("id", ""),
                "title": entry.get("title", ""),
                "published_at": entry.get("upload_date", ""),
                "thumbnail_url": entry.get("thumbnail", ""),
            })
        return items

    loop = asyncio.get_running_loop()
    return await asyncio.wait_for(
        loop.run_in_executor(_get_ytdlp_executor(), _extract),
        timeout=45,
    )

# =============================================================================
# Channel Discovery 引擎 —— 潜力新号发现
# =============================================================================

def _parse_int(value: Any) -> int | None:
    """安全解析整数."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _calculate_viral_score(
    subscriber_count: int | None,
    video_count: int | None,
    total_views: int | None,
    channel_age_months: float | None,
) -> float:
    """计算频道评分 (0-100) — 基于播放量和规模，不再惩罚大频道.

    核心逻辑:
      - 总播放量评分 (0-40): 总量越大分越高
      - 平均播放量评分 (0-40): 均播越高分越高
      - 订阅数评分 (0-20): 订阅越多分越高
    """
    import math

    # 把 None 转为 0，让有 subscriber_count 的频道也能得分
    subscriber_count = subscriber_count or 0
    video_count = video_count or 0
    total_views = total_views or 0

    if subscriber_count == 0 and video_count == 0 and total_views == 0:
        return 0.0

    avg_views = total_views / max(video_count, 1)

    # 总播放量评分: 1B views = 40分, 1M = 24分, 1K = 8分
    view_score = min(40.0, math.log10(total_views + 1) / 9.0 * 40.0)

    # 平均播放量评分: 1M avg = 40分, 100K = 33分, 10K = 27分, 1K = 20分
    avg_score = min(40.0, math.log10(avg_views + 1) / 6.0 * 40.0)

    # 订阅数评分: 10M subs = 20分, 1M = 14分, 100K = 7分
    sub_score = min(20.0, math.log10(subscriber_count + 1) / 7.0 * 20.0)

    score = view_score + avg_score + sub_score
    return min(100.0, max(0.0, score))


async def _update_run_progress(
    session: AsyncSession, run_id: int | None, message: str, items_found: int = 0
) -> None:
    """更新 CrawlerTaskRun 的进度消息（供前端轮询展示）."""
    if not run_id:
        return
    try:
        from packages.db.schema import CrawlerTaskRun
        run = await session.get(CrawlerTaskRun, run_id)
        if run:
            run.message = message
            run.items_found = items_found
            await session.commit()
    except Exception as exc:
        logger.warning(f"Failed to update run progress: {exc}")


async def _execute_channel_discovery(
    task: CrawlerTask, session: AsyncSession, run_id: int | None = None
) -> dict[str, Any]:
    """执行频道发现任务：批量关键词搜索 → 提取频道 → 评分 → 入库."""
    # ── 1. 解析配置 ──
    config: dict[str, Any] = {}
    if task.config_json:
        try:
            config = json.loads(task.config_json)
        except json.JSONDecodeError:
            pass

    keywords = config.get("keywords", [])
    if not keywords and task.target:
        # fallback: target 作为逗号分隔的关键词列表
        keywords = [k.strip() for k in task.target.split(",") if k.strip()]

    if not keywords:
        return {
            "source_status": "error",
            "message": "No keywords provided for discovery.",
            "items": [],
        }

    max_results_per_keyword = config.get(
        "max_results_per_keyword", settings.CRAWLER_DEFAULT_MAX_RESULTS
    )
    # 硬性筛选已取消，所有频道都入库，评分排序让高播放频道排在前面
    max_channel_age_months = config.get("max_channel_age_months", 240)
    max_video_count = config.get("max_video_count", 9999)

    extractor = DualTrackExtractor(api_key=settings.YOUTUBE_API_KEY)

    all_discovered: list[dict[str, Any]] = []
    total_found = 0
    total_passed = 0

    # ── 内部：并发搜索单个关键词（直接搜频道） ──
    _search_sem = asyncio.Semaphore(1)  # 串行搜索，避免代理 SSL 握手冲突

    async def _search_channels_http_local(keyword: str) -> list[dict[str, Any]]:
        """通过 YouTube 搜索结果页抓取频道列表（零配额），带 429 重试."""
        loop = asyncio.get_running_loop()

        def _fetch() -> list[dict[str, Any]]:
            http = _get_http_client()
            q = keyword.replace(" ", "+")
            url = f"https://www.youtube.com/results?search_query={q}&sp=EgIQAg%3D%3D"
            for attempt in range(3):
                resp, content = http.request(url, method="GET", headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                if resp.status == 429:
                    import time
                    time.sleep(5 + attempt * 5)
                    continue
                if resp.status != 200:
                    logger.warning(f"HTTP search status {resp.status} for '{keyword}'")
                    return []
                html = content.decode("utf-8", errors="ignore")
                match = re.search(r'var ytInitialData = ({.+?});</script>', html)
                if not match:
                    logger.warning(f"HTTP search: no ytInitialData for '{keyword}'")
                    return []
                data = json.loads(match.group(1))
                items = []
                contents = data.get("contents", {}).get("twoColumnSearchResultsRenderer", {}).get("primaryContents", {}).get("sectionListRenderer", {}).get("contents", [])
                for section in contents:
                    section_items = section.get("itemSectionRenderer", {}).get("contents", [])
                    for item in section_items:
                        ch = item.get("channelRenderer")
                        if ch and ch.get("channelId"):
                            # 从搜索结果中提取订阅数（如果有）
                            sub_text = ch.get("subscriberCountText", {}).get("simpleText", "")
                            sub_count = 0
                            if sub_text:
                                # 解析 "1.2M subscribers" / "1.52K" / "No subscribers"
                                import re as _re
                                m = _re.search(r'([\d.]+)\s*([KMB]?)', sub_text.replace(",", ""))
                                if m and m.group(1) != ".":
                                    try:
                                        num = float(m.group(1))
                                        unit = m.group(2)
                                        sub_count = int(num * {"K": 1000, "M": 1000000, "B": 1000000000}.get(unit, 1))
                                    except ValueError:
                                        sub_count = 0
                            items.append({
                                "id": {"channelId": ch["channelId"]},
                                "snippet": {
                                    "title": ch.get("title", {}).get("simpleText", ""),
                                    "description": "",
                                    "thumbnails": ch.get("thumbnail", {}),
                                },
                                "subscriber_count": sub_count,
                            })
                return items
            return []

        return await loop.run_in_executor(None, _fetch)

    async def _search_single_keyword(keyword: str) -> tuple[str, list[dict[str, Any]]]:
        """搜索单个关键词，优先用 HTTP 网页抓取（零配额），fallback 到 API."""
        async with _search_sem:
            logger.info(f"Discovery: searching keyword '{keyword}' (type=channel)")
            search_items: list[dict[str, Any]] = []

            # 1. 优先用 HTTP 网页抓取（零配额，已验证稳定）
            try:
                search_items = await asyncio.wait_for(
                    _search_channels_http_local(keyword),
                    timeout=20,
                )
            except asyncio.TimeoutError:
                logger.warning(f"HTTP search timeout for '{keyword}'")
            except Exception as exc:
                logger.warning(f"HTTP search failed for '{keyword}': {exc}")

            # 2. HTTP 失败且还有 API 配额时 fallback 到 API
            if not search_items and settings.YOUTUBE_API_KEY:
                try:
                    api_result = await asyncio.wait_for(
                        extractor._api.search_list(
                            keyword,
                            max_results=max_results_per_keyword,
                            search_type="channel",
                            order="viewCount",
                        ),
                        timeout=15,
                    )
                    if "error" not in api_result:
                        search_items = api_result.get("items", [])
                except asyncio.TimeoutError:
                    logger.warning(f"API search timeout for '{keyword}'")
                except Exception as exc:
                    logger.warning(f"API search failed for '{keyword}': {exc}")

            # 搜索间加 2 秒延迟，避免 YouTube 429 限流
            await asyncio.sleep(2)
            return keyword, search_items

    # ── 2. 并发搜索所有关键词 ──
    logger.info(f"Discovery: starting concurrent search for {len(keywords)} keywords")
    search_results = await asyncio.gather(
        *[_search_single_keyword(kw) for kw in keywords],
        return_exceptions=True,
    )

    # 收集所有频道 ID 和搜索映射（搜频道时 item.id.channelId 直接是频道ID）
    keyword_to_items: dict[str, list[dict[str, Any]]] = {}
    all_channel_ids: set[str] = set()
    for result in search_results:
        if isinstance(result, Exception):
            logger.warning(f"Keyword search failed: {result}")
            continue
        kw, items = result
        if not items:
            continue
        keyword_to_items[kw] = items
        for item in items:
            cid = item.get("id", {}).get("channelId") or item.get("snippet", {}).get("channelId")
            if cid:
                all_channel_ids.add(cid)

    if not all_channel_ids:
        return {
            "source_status": "empty",
            "message": f"No channels found across {len(keywords)} keywords.",
            "items": [],
            "channels_found": 0,
            "channels_passed": 0,
            "keywords": keywords,
        }

    logger.info(f"Discovery: found {len(all_channel_ids)} unique channels, fetching details")
    await _update_run_progress(
        session, run_id,
        f"搜索完成，发现 {len(all_channel_ids)} 个频道，正在获取详情...",
        items_found=0,
    )

    # ── 3. 批量获取频道详情 ──
    detail_items: dict[str, dict[str, Any]] = {}
    try:
        detail_result = await extractor.get_channel_details(list(all_channel_ids))
        detail_items = {
            item["id"]: item
            for item in detail_result.get("items", [])
            if item.get("id")
        }
    except Exception as exc:
        logger.warning(f"Failed to get channel details: {exc}")

    # API 配额耗尽时，用搜索结果中的数据构建简化版详情
    if len(detail_items) < len(all_channel_ids) * 0.5:
        logger.info(f"API details insufficient ({len(detail_items)}/{len(all_channel_ids)}), using search result fallback")
        for kw, items in keyword_to_items.items():
            for item in items:
                cid = item.get("id", {}).get("channelId") or item.get("snippet", {}).get("channelId")
                if cid and cid not in detail_items:
                    detail_items[cid] = {
                        "id": cid,
                        "snippet": item.get("snippet", {}),
                        "statistics": {
                            "subscriberCount": str(item.get("subscriber_count", 0) or 0),
                            "videoCount": "0",
                            "viewCount": "0",
                        },
                    }

    await _update_run_progress(
        session, run_id,
        f"获取详情完成 ({len(detail_items)}/{len(all_channel_ids)})，正在评分筛选...",
        items_found=0,
    )

    # ── 4. 评分和筛选 ──
    for cid in all_channel_ids:
        detail = detail_items.get(cid)
        if not detail:
            continue

        snippet = detail.get("snippet", {})
        stats = detail.get("statistics", {})

        title = snippet.get("title", "")
        subscriber_count = _parse_int(stats.get("subscriberCount"))
        video_count = _parse_int(stats.get("videoCount"))
        total_views = _parse_int(stats.get("viewCount"))

        # 频道创建时间
        channel_published = snippet.get("publishedAt")
        channel_created_at: datetime | None = None
        channel_age_months: float | None = None
        if channel_published:
            try:
                channel_created_at = datetime.fromisoformat(
                    channel_published.replace("Z", "+00:00")
                )
                channel_age_months = (
                    datetime.now(timezone.utc) - channel_created_at
                ).days / 30.0
            except ValueError:
                pass

        # 计算平均播放量
        avg_views = (
            total_views / max(video_count, 1)
            if total_views and video_count
            else 0
        )

        total_found += 1

        # ── 软性筛选（只过滤明显无效的，不卡播放量） ──
        if video_count and video_count > 9999:
            continue
        if channel_age_months and channel_age_months > 240:
            continue

        # ── 计算评分（高播放量/高订阅频道得分更高） ──
        score = _calculate_viral_score(
            subscriber_count=subscriber_count,
            video_count=video_count,
            total_views=total_views,
            channel_age_months=channel_age_months,
        )

        # ── 确定来源关键词 ──
        source_keyword = ""
        fallback_snippet = {}
        for kw, items in keyword_to_items.items():
            for item in items:
                item_cid = item.get("id", {}).get("channelId") or item.get("snippet", {}).get("channelId")
                if item_cid == cid:
                    source_keyword = kw
                    fallback_snippet = item.get("snippet", {})
                    break
            if source_keyword:
                break

        # ── 收集入库数据 ──
        all_discovered.append({
            "youtube_id": cid,
            "title": title,
            "score": round(score, 2),
            "subscriber_count": subscriber_count,
            "video_count": video_count,
            "avg_views": int(avg_views),
            "channel_age_months": round(channel_age_months, 1) if channel_age_months else None,
            "source_keyword": source_keyword,
            "fallback_snippet": fallback_snippet,
            "detail": detail,
            "subscriber_count_raw": subscriber_count,
            "video_count_raw": video_count,
            "total_views_raw": total_views,
            "avg_views_raw": avg_views,
            "channel_created_at_raw": channel_created_at,
        })
        total_passed += 1

    # ── 5. 批量入库 / 更新 ──
    now = datetime.now(timezone.utc)

    # 5a. 批量查询已存在的频道（减少 N+1 查询）
    discovered_ids = [d["youtube_id"] for d in all_discovered]
    existing_result = await session.execute(
        select(Channel).where(Channel.youtube_id.in_(discovered_ids))
    )
    existing_map: dict[str, Channel] = {
        ch.youtube_id: ch for ch in existing_result.scalars().all()
    }

    new_channels: list[Channel] = []

    for disc in all_discovered:
        cid = disc["youtube_id"]
        existing = existing_map.get(cid)
        if existing:
            existing.subscriber_count = disc["subscriber_count_raw"]
            existing.video_count = disc["video_count_raw"]
            existing.view_count = disc["total_views_raw"]
            existing.avg_views_per_video = int(disc["avg_views_raw"])
            existing.discovery_score = disc["score"]
            existing.discovery_keyword = disc["source_keyword"]
            existing.discovered_at = now
            existing.last_stats_updated = now
            if disc["channel_created_at_raw"]:
                existing.channel_created_at = disc["channel_created_at_raw"]
            disc["channel_id"] = existing.id
        else:
            new_ch = Channel(
                **build_channel_values(cid, disc["fallback_snippet"], disc["detail"])
            )
            new_ch.subscriber_count = disc["subscriber_count_raw"]
            new_ch.video_count = disc["video_count_raw"]
            new_ch.view_count = disc["total_views_raw"]
            new_ch.avg_views_per_video = int(disc["avg_views_raw"])
            new_ch.discovery_score = disc["score"]
            new_ch.discovery_keyword = disc["source_keyword"]
            new_ch.discovered_at = now
            new_ch.last_stats_updated = now
            if disc["channel_created_at_raw"]:
                new_ch.channel_created_at = disc["channel_created_at_raw"]
            new_channels.append(new_ch)
            disc["channel_id"] = 0  # placeholder, updated after flush

    # 5b. 批量插入新频道（一次 flush）
    if new_channels:
        session.add_all(new_channels)
        await session.flush()
        new_id_map = {ch.youtube_id: ch.id for ch in new_channels}
        for disc in all_discovered:
            if disc["channel_id"] == 0:
                disc["channel_id"] = new_id_map[disc["youtube_id"]]

    # 5c. 批量创建 discovery results（绑定到本次 run）
    if run_id and all_discovered:
        all_discovered.sort(key=lambda x: x["score"], reverse=True)
        discovery_results = []
        for rank, disc in enumerate(all_discovered, start=1):
            discovery_results.append(ChannelDiscoveryResult(
                crawler_task_run_id=run_id,
                channel_id=disc["channel_id"],
                keyword=disc["source_keyword"],
                viral_score=disc["score"],
                rank=rank,
            ))
        session.add_all(discovery_results)

    await session.commit()

    # ── 6. 自动创建 ContentProject（高潜频道）──
    auto_projects: list[ContentProject] = []
    if run_id:
        for disc in all_discovered:
            if disc.get("score", 0) >= 70:
                desc_lines = [
                    f"频道: {disc.get('title', 'Unknown')}",
                    f"评分: {disc.get('score')}",
                    f"订阅: {disc.get('subscriber_count') or 'N/A'}",
                    f"视频数: {disc.get('video_count') or 'N/A'}",
                    f"平均播放: {disc.get('avg_views') or 'N/A'}",
                    f"来源关键词: {disc.get('source_keyword', '')}",
                ]
                project = ContentProject(
                    title=f"[发现] {disc.get('title', 'Unknown')} — {disc.get('score')}分",
                    description="\n".join(desc_lines),
                    source_crawler_task_id=task.id,
                    source_run_id=run_id,
                    status="draft",
                )
                auto_projects.append(project)
        if auto_projects:
            session.add_all(auto_projects)
            await session.commit()
            logger.info(f"Auto-created {len(auto_projects)} ContentProjects from discovery run {run_id}")

    await _update_run_progress(
        session, run_id,
        f"入库完成，共发现 {total_passed} 个高潜频道" + (f"，自动创建 {len(auto_projects)} 个项目" if auto_projects else ""),
        items_found=total_passed,
    )

    # ── 7. 清理临时字段，按评分排序返回 ──
    for disc in all_discovered:
        disc.pop("fallback_snippet", None)
        disc.pop("detail", None)
        disc.pop("subscriber_count_raw", None)
        disc.pop("video_count_raw", None)
        disc.pop("total_views_raw", None)
        disc.pop("avg_views_raw", None)
        disc.pop("channel_created_at_raw", None)

    all_discovered.sort(key=lambda x: x["score"], reverse=True)

    return {
        "source_status": "success",
        "message": (
            f"Discovery completed. Scanned {len(keywords)} keywords, "
            f"found {total_found} channels, {total_passed} passed filters."
        ),
        "items": all_discovered,
        "channels_found": total_found,
        "channels_passed": total_passed,
        "keywords": keywords,
    }
