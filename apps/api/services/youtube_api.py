"""
YouTube Data API v3 瀹㈡埛绔?+ yt-dlp 闄嶇骇鍙岃建鏂规

鏍稿績璁捐:
  1. YouTubeAPIClient: 瀹樻柟 API 璋冪敤, 甯﹂厤棰濈鐞嗕笌鎵归噺浼樺寲
  2. QuotaManager: 姣忔棩閰嶉杩借釜涓庨璀?  3. AsyncYTDLPMetaExtractor: yt-dlp 寮傛鍏冩暟鎹彁鍙?(闆堕厤棰濋檷绾?
  4. DualTrackExtractor: 鏅鸿兘鍙岃建璋冨害 (API浼樺厛, 閰嶉鑰楀敖鑷姩闄嶇骇)

閰嶉浼樺寲绛栫暐:
  - videos.list 鎵归噺 50 ID/call (浠?1 鍗曚綅)
  - 閬垮厤 search.list (100 鍗曚綅/娆?
  - 鐢?playlistItems.list 鑾峰彇棰戦亾鏂拌棰?"""
from __future__ import annotations

import asyncio

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# 鈹€鈹€ 閰嶉绠＄悊 鈹€鈹€

class EndpointCost(Enum):
    """YouTube Data API v3 endpoint 閰嶉娑堣€?(鍗曚綅/娆?."""
    SEARCH_LIST = 100
    VIDEOS_LIST = 1
    CHANNELS_LIST = 1
    PLAYLISTITEMS_LIST = 1
    COMMENTTHREADS_LIST = 1
    ACTIVITIES_LIST = 1


@dataclass(slots=True)
class QuotaSnapshot:
    """閰嶉娑堣€楃姸鎬佸揩鐓?(涓嶅彲鍙樻洿鏂?."""
    units_consumed: int = 0
    units_remaining: int = 10000
    last_reset_utc: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    call_log: list[tuple[datetime, str, int]] = field(default_factory=list)

    def with_call(self, endpoint: str, cost: int) -> QuotaSnapshot:
        now = datetime.now(timezone.utc)
        new_log = self.call_log + [(now, endpoint, cost)]
        return QuotaSnapshot(
            units_consumed=self.units_consumed + cost,
            units_remaining=max(0, self.units_remaining - cost),
            last_reset_utc=self.last_reset_utc,
            call_log=new_log,
        )

    def is_exhausted(self, buffer: int = 50) -> bool:
        return self.units_remaining <= buffer

    def reset_if_needed(self) -> QuotaSnapshot:
        now_utc = datetime.now(timezone.utc)
        pt_offset = timedelta(hours=7 if hasattr(__import__("time"), "daylight") and __import__("time").daylight else 8)
        now_pt = now_utc - pt_offset
        reset_pt = self.last_reset_utc - pt_offset
        if now_pt.date() != reset_pt.date():
            return QuotaSnapshot(
                units_consumed=0, units_remaining=10000,
                last_reset_utc=now_utc, call_log=[],
            )
        return self


class QuotaManager:
    """閰嶉棰勭畻绠＄悊鍣?(鍗忕▼瀹夊叏, 閫傜敤浜庡崟杩涚▼鍦烘櫙)."""

    DEFAULT_DAILY_QUOTA = 10_000

    def __init__(self, daily_quota: int = DEFAULT_DAILY_QUOTA) -> None:
        self._daily_quota = daily_quota
        self._snapshot = QuotaSnapshot(
            units_consumed=0, units_remaining=daily_quota,
            last_reset_utc=datetime.now(timezone.utc), call_log=[],
        )
        self._lock = asyncio.Lock()

    @property
    def snapshot(self) -> QuotaSnapshot:
        return self._snapshot.reset_if_needed()

    async def record(self, endpoint: EndpointCost | str, cost: int | None = None) -> None:
        async with self._lock:
            if isinstance(endpoint, EndpointCost):
                name, cost = endpoint.name, endpoint.value
            else:
                name = endpoint
                cost = cost or 1
            self._snapshot = self._snapshot.with_call(name, cost)

    async def check_budget(self, needed: int = 1) -> bool:
        snap = self.snapshot
        return not snap.is_exhausted(buffer=needed)

    async def get_usage_report(self) -> dict[str, Any]:
        snap = self.snapshot
        endpoint_totals: dict[str, int] = {}
        for _, ep, cost in snap.call_log:
            endpoint_totals[ep] = endpoint_totals.get(ep, 0) + cost
        return {
            "units_consumed": snap.units_consumed,
            "units_remaining": snap.units_remaining,
            "usage_pct": round(snap.units_consumed / self._daily_quota * 100, 2),
            "endpoints": endpoint_totals,
            "calls_total": len(snap.call_log),
            "next_reset_pt": "Midnight Pacific Time",
        }


# 鈹€鈹€ YouTube API Client 鈹€鈹€

class YouTubeAPIClient:
    """甯﹂厤棰濊拷韪殑 YouTube Data API v3 寮傛瀹㈡埛绔?

    鐗规€?
      - 鑷姩鎵归噺鍒嗗潡 (videos.list 姣忓潡 50 ID)
      - 閰嶉棰勬涓庢秷鑰楄褰?      - 寮傛鍖栧鐞嗘墍鏈夌綉缁滆姹?    """

    def __init__(
        self,
        api_key: str | None = None,
        quota: QuotaManager | None = None,
    ) -> None:
        from apps.api.config import settings
        self._api_key = api_key or os.environ.get("YOUTUBE_API_KEY") or settings.YOUTUBE_API_KEY or ""
        self._quota = quota or QuotaManager()
        self._youtube = None
        if self._api_key:
            try:
                from googleapiclient.discovery import build
                self._youtube = build(
                    "youtube", "v3",
                    developerKey=self._api_key,
                    cache_discovery=False,
                )
            except ImportError:
                logger.warning("google-api-python-client not installed, API mode unavailable")

    @property
    def quota(self) -> QuotaManager:
        return self._quota

    def _is_available(self) -> bool:
        return self._youtube is not None and bool(self._api_key)

    async def videos_list(
        self,
        ids: list[str],
        parts: list[str] | None = None,
    ) -> dict[str, Any]:
        """鎵归噺鑾峰彇瑙嗛璇︽儏 (1 unit per call, max 50 IDs/call)."""
        if not self._is_available():
            return {"items": [], "error": "API not available"}

        has_budget = await self._quota.check_budget(needed=EndpointCost.VIDEOS_LIST.value)
        if not has_budget:
            return {"items": [], "error": "quota_exhausted"}

        if not ids:
            return {"items": []}

        parts = parts or ["snippet", "statistics", "contentDetails"]
        loop = asyncio.get_running_loop()
        all_items: list[dict[str, Any]] = []

        for i in range(0, len(ids), 50):
            chunk = ids[i:i + 50]
            has_budget = await self._quota.check_budget(
                needed=EndpointCost.VIDEOS_LIST.value
            )
            if not has_budget:
                break

            def _fetch(chunk_ids: list[str]) -> dict[str, Any]:
                resp = (
                    self._youtube.videos()
                    .list(part=",".join(parts), id=",".join(chunk_ids))
                    .execute()
                )
                return resp

            response = await loop.run_in_executor(None, _fetch, chunk)
            await self._quota.record(EndpointCost.VIDEOS_LIST)
            all_items.extend(response.get("items", []))

        return {"items": all_items, "total": len(all_items)}

    async def channels_list(
        self,
        ids: list[str] | None = None,
        handles: list[str] | None = None,
        parts: list[str] | None = None,
    ) -> dict[str, Any]:
        """鑾峰彇棰戦亾璇︽儏 (1 unit per call)."""
        if not self._is_available():
            return {"items": [], "error": "API not available"}

        has_budget = await self._quota.check_budget(
            needed=EndpointCost.CHANNELS_LIST.value
        )
        if not has_budget:
            return {"items": [], "error": "quota_exhausted"}

        parts = parts or ["snippet", "statistics", "brandingSettings"]
        kwargs: dict[str, str] = {"part": ",".join(parts)}
        if ids:
            kwargs["id"] = ",".join(ids[:50])
        elif handles:
            kwargs["forHandle"] = ",".join(handles[:50])
        else:
            raise ValueError("Either ids or handles must be provided")

        loop = asyncio.get_running_loop()

        def _fetch() -> dict[str, Any]:
            return self._youtube.channels().list(**kwargs).execute()

        response = await loop.run_in_executor(None, _fetch)
        await self._quota.record(EndpointCost.CHANNELS_LIST)
        return response

    async def playlist_items_list(
        self,
        playlist_id: str,
        max_results: int = 50,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        """鑾峰彇鎾斁鍒楄〃鍐呭 (1 unit per call) 鈥?鐢ㄤ簬鑾峰彇棰戦亾鏈€鏂拌棰?"""
        if not self._is_available():
            return {"items": [], "error": "API not available"}

        has_budget = await self._quota.check_budget(
            needed=EndpointCost.PLAYLISTITEMS_LIST.value
        )
        if not has_budget:
            return {"items": [], "error": "quota_exhausted"}

        kwargs: dict[str, Any] = {
            "part": "snippet,contentDetails",
            "playlistId": playlist_id,
            "maxResults": min(max_results, 50),
        }
        if page_token:
            kwargs["pageToken"] = page_token

        loop = asyncio.get_running_loop()

        def _fetch() -> dict[str, Any]:
            return self._youtube.playlistItems().list(**kwargs).execute()

        response = await loop.run_in_executor(None, _fetch)
        await self._quota.record(EndpointCost.PLAYLISTITEMS_LIST)
        return response


# 鈹€鈹€ yt-dlp 闄嶇骇鏂规 鈹€鈹€

@dataclass(slots=True, frozen=True)
class VideoMetadata:
    """鏍囧噯鍖栬棰戝厓鏁版嵁缁撴瀯."""
    video_id: str
    title: str
    description: str | None
    channel_id: str | None
    channel_title: str | None
    upload_date: str | None  # YYYYMMDD
    duration_seconds: int | None
    view_count: int | None
    like_count: int | None
    comment_count: int | None
    tags: list[str]
    categories: list[str]
    thumbnail_url: str | None
    language: str | None
    is_live: bool
    availability: str | None


class YTDLPMetaExtractor:
    """鍩轰簬 yt-dlp 鐨勫厓鏁版嵁鎻愬彇鍣?(闆堕厤棰?."""

    DEFAULT_OPTS: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "ignore_no_formats_error": True,
        "extract_flat": False,
    }

    def __init__(self, options: dict[str, Any] | None = None) -> None:
        self._opts = {**self.DEFAULT_OPTS, **(options or {})}

    def extract_video(self, url: str) -> VideoMetadata:
        import yt_dlp
        with yt_dlp.YoutubeDL(self._opts) as ydl:
            info: dict[str, Any] = ydl.extract_info(url, download=False)
            return self._normalize(info)

    def extract_playlist(self, url: str, max_entries: int | None = None) -> list[VideoMetadata]:
        import yt_dlp
        opts = dict(self._opts)
        if max_entries:
            opts["playlistend"] = max_entries
        with yt_dlp.YoutubeDL(opts) as ydl:
            info: dict[str, Any] = ydl.extract_info(url, download=False)
            entries = info.get("entries", []) or []
            return [self._normalize(e) for e in entries if e]

    def extract_channel_uploads(
        self, channel_url: str, max_videos: int = 50,
    ) -> list[VideoMetadata]:
        import yt_dlp
        opts = {**self._opts, "playlistend": max_videos}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info: dict[str, Any] = ydl.extract_info(
                f"{channel_url}/videos", download=False
            )
            entries = info.get("entries", []) or []
            return [self._normalize(e) for e in entries if e]

    @staticmethod
    def _normalize(info: dict[str, Any]) -> VideoMetadata:
        return VideoMetadata(
            video_id=info.get("id", ""),
            title=info.get("title", ""),
            description=info.get("description"),
            channel_id=info.get("channel_id"),
            channel_title=info.get("channel"),
            upload_date=info.get("upload_date"),
            duration_seconds=info.get("duration"),
            view_count=info.get("view_count"),
            like_count=info.get("like_count"),
            comment_count=info.get("comment_count"),
            tags=info.get("tags", []) or [],
            categories=info.get("categories", []) or [],
            thumbnail_url=info.get("thumbnail"),
            language=info.get("language"),
            is_live=bool(info.get("is_live")),
            availability=info.get("availability"),
        )


class AsyncYTDLPMetaExtractor:
    """寮傛 yt-dlp 鍏冩暟鎹彁鍙栧櫒 (閫氳繃 run_in_executor 瀹炵幇闈為樆濉?."""

    def __init__(self, options: dict[str, Any] | None = None) -> None:
        self._opts = {**YTDLPMetaExtractor.DEFAULT_OPTS, **(options or {})}

    async def extract_video(self, url: str) -> VideoMetadata:
        loop = asyncio.get_running_loop()
        extractor = YTDLPMetaExtractor(self._opts)
        return await loop.run_in_executor(None, extractor.extract_video, url)

    async def batch_extract(
        self,
        urls: list[str],
        max_concurrency: int = 3,
    ) -> list[VideoMetadata | Exception]:
        semaphore = asyncio.Semaphore(max_concurrency)

        async def _fetch(url: str) -> VideoMetadata | Exception:
            async with semaphore:
                try:
                    return await self.extract_video(url)
                except Exception as e:
                    return e

        return await asyncio.gather(*[_fetch(u) for u in urls])


# 鈹€鈹€ 鍙岃建璋冨害鍣?鈹€鈹€

class DualTrackExtractor:
    """鏅鸿兘鍙岃建鎻愬彇鍣? API 浼樺厛, 閰嶉鑰楀敖鑷姩闄嶇骇鍒?yt-dlp / CrawlerEngine.

    浣跨敤绛栫暐:
      1. 妫€鏌?API 閰嶉
      2. 鏈夐厤棰?-> 浣跨敤 YouTubeAPIClient (鏇村揩鏇寸ǔ瀹?
      3. 鏃犻厤棰?/ API 涓嶅彲鐢?-> 闄嶇骇鍒?AsyncYTDLPMetaExtractor (闆堕厤棰?
      4. 缃戦〉绾ф姄鍙?-> 浣跨敤 CrawlerEngine (甯﹀弽鐖瓥鐣?
    """

    def __init__(
        self,
        api_key: str | None = None,
        quota: QuotaManager | None = None,
    ) -> None:
        self._api = YouTubeAPIClient(api_key=api_key, quota=quota)
        self._yt_dlp = AsyncYTDLPMetaExtractor()
        self._quota = quota or self._api.quota
        # 闆嗘垚鐢熶骇绾х埇铏紩鎿?        from apps.api.services.crawler_engine import CrawlerEngine, CrawlerPolicy
        # CRG: Channel search now relies on the official API; no crawler dependency during startup.

    @property
    def quota(self) -> QuotaManager:
        return self._quota

    async def get_video_details(self, video_ids: list[str]) -> dict[str, Any]:
        """鑾峰彇瑙嗛璇︽儏 (鑷姩閫夋嫨鏈€浼橀€氶亾)."""
        has_quota = await self._quota.check_budget(needed=1)

        if has_quota and self._api._is_available():
            logger.info(f"Using API for {len(video_ids)} videos")
            result = await self._api.videos_list(ids=video_ids)
            if "error" not in result or not result.get("error"):
                return result
            logger.warning(f"API failed, falling back to yt-dlp: {result.get('error')}")

        # yt-dlp 闄嶇骇
        logger.info(f"Using yt-dlp fallback for {len(video_ids)} videos")
        urls = [f"https://www.youtube.com/watch?v={vid}" for vid in video_ids]
        results = await self._yt_dlp.batch_extract(urls, max_concurrency=3)
        items = []
        for r in results:
            if isinstance(r, VideoMetadata):
                items.append({
                    "id": r.video_id,
                    "snippet": {
                        "title": r.title,
                        "description": r.description,
                        "channelId": r.channel_id,
                        "channelTitle": r.channel_title,
                        "publishedAt": r.upload_date,
                        "thumbnails": {
                            "high": {"url": r.thumbnail_url}
                        } if r.thumbnail_url else {},
                        "tags": r.tags,
                        "categoryId": r.categories[0] if r.categories else None,
                    },
                    "statistics": {
                        "viewCount": r.view_count,
                        "likeCount": r.like_count,
                        "commentCount": r.comment_count,
                    },
                    "contentDetails": {
                        "duration": r.duration_seconds,
                    },
                })
        return {"items": items, "total": len(items), "source": "yt_dlp"}

    async def get_channel_details(self, channel_ids: list[str]) -> dict[str, Any]:
        """鑾峰彇棰戦亾璇︽儏 (鑷姩閫夋嫨鏈€浼橀€氶亾)."""
        has_quota = await self._quota.check_budget(needed=1)

        if has_quota and self._api._is_available():
            result = await self._api.channels_list(ids=channel_ids)
            if "error" not in result or not result.get("error"):
                return result

        # yt-dlp 闄嶇骇: 閫氳繃棰戦亾椤甸潰鎻愬彇
        logger.info(f"Using yt-dlp fallback for {len(channel_ids)} channels")
        urls = [f"https://www.youtube.com/channel/{cid}" for cid in channel_ids]
        results = await self._yt_dlp.batch_extract(urls, max_concurrency=2)
        items = []
        for r in results:
            if isinstance(r, VideoMetadata) and r.channel_id:
                items.append({
                    "id": r.channel_id,
                    "snippet": {
                        "title": r.channel_title or "Unknown",
                        "description": r.description,
                    },
                    "statistics": {
                        "subscriberCount": None,
                        "videoCount": None,
                        "viewCount": r.view_count,
                    },
                })
        return {"items": items, "total": len(items), "source": "yt_dlp"}

    async def search_channels(
        self, query: str, max_results: int = 5
    ) -> dict[str, Any]:
        """鎼滅储棰戦亾 鈥?API 浼樺厛, 闄嶇骇鍒?CrawlerEngine 缃戦〉鎶撳彇.

        Returns:
            {"items": [{"snippet": {"channelId": ..., "title": ..., ...}}], "source": "api|web"}
        """
        has_quota = await self._quota.check_budget(needed=EndpointCost.SEARCH_LIST.value)

        if has_quota and self._api._is_available():
            try:
                loop = asyncio.get_running_loop()

                def _fetch() -> dict[str, Any]:
                    return (
                        self._api._youtube.search()
                        .list(part="snippet", q=query, type="channel", maxResults=max_results)
                        .execute()
                    )

                result = await loop.run_in_executor(None, _fetch)
                await self._quota.record(EndpointCost.SEARCH_LIST)
                return {"items": result.get("items", []), "source": "api"}
            except Exception as e:
                # CRG: Do not parse YouTube HTML with brittle regex; callers need the real API failure.
                raise RuntimeError(f"YouTube channel search failed: {e}") from e

        # CrawlerEngine 缃戦〉鎶撳彇闄嶇骇
        # CRG: Empty quota/API availability is an integration failure, not an empty search result.
        raise RuntimeError("YouTube channel search unavailable: API key missing, invalid, or quota exhausted")

    async def get_comments(self, video_id: str, max_results: int = 20) -> list[tuple[str, str]]:
        """鑾峰彇瑙嗛璇勮 鈥?API 浼樺厛, 闄嶇骇鍒?CrawlerEngine.

        Returns:
            [(comment_id, text), ...]
        """
        # 灏濊瘯 API
        has_quota = await self._quota.check_budget(needed=EndpointCost.COMMENTTHREADS_LIST.value)
        if has_quota and self._api._is_available():
            try:
                loop = asyncio.get_running_loop()

                def _fetch() -> dict[str, Any]:
                    return (
                        self._api._youtube.commentThreads()
                        .list(part="snippet", videoId=video_id, maxResults=max_results, order="relevance")
                        .execute()
                    )

                result = await loop.run_in_executor(None, _fetch)
                await self._quota.record(EndpointCost.COMMENTTHREADS_LIST)
                comments = []
                for item in result.get("items", []):
                    snippet = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
                    text = snippet.get("textDisplay", "")
                    cid = item.get("id", "")
                    if text:
                        comments.append((cid, text))
                return comments
            except Exception as e:
                # CRG: Comment analysis must distinguish fetch failure from a video with zero comments.
                raise RuntimeError(f"YouTube comments fetch failed: {e}") from e

        # yt-dlp 闄嶇骇
        # CRG: yt-dlp does not provide comments here, so returning [] would corrupt sentiment analysis.
        raise RuntimeError("YouTube comments unavailable: API key missing, invalid, or quota exhausted")
