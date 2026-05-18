from __future__ import annotations

"""YouTube 访问层兼容入口。

这个模块保留旧导入路径，但把职责拆到更小的实现里：
- `youtube_client.py`：API 客户端与代理探测
- `youtube_quota.py`：配额与 Key 池
- `youtube_core.py`：阻塞执行器与共享工具

为了尽量不影响现有调用方，这里提供一个轻量 facade：
`YouTubeAPIClient` 继续承载最常用的方法，内部委托给更小的模块。
"""

import asyncio
import logging
import os
import re
from datetime import datetime, timedelta
from typing import Any

import httpx

from apps.api.config import settings
from apps.api.services.youtube_client import YouTubeAPIClient, is_proxy_reachable
from apps.api.services.youtube_core import close_youtube_executor, get_blocking_executor
from apps.api.services.youtube_quota import EndpointCost, KeyPoolManager, QuotaManager

logger = logging.getLogger(__name__)


class VideoMetadata:
    def __init__(self, **kwargs: Any) -> None:
        self.__dict__.update(kwargs)


class YTDLPMetaExtractor:
    pass


class AsyncYTDLPMetaExtractor:
    pass


class DualTrackExtractor:
    pass


class FallbackScraper:
    BASE_YOUTUBE_URL = "https://www.youtube.com"

    def __init__(self) -> None:
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]

    def _get_headers(self) -> dict[str, str]:
        return {
            "User-Agent": self.user_agents[0],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

    async def search_channels_fallback(self, query: str, max_results: int = 20) -> list[dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=5.0), follow_redirects=True) as client:
                await client.get(
                    f"{self.BASE_YOUTUBE_URL}/results?search_query={query.replace(' ', '+')}&sp=EgIQAg%253D%253D",
                    headers=self._get_headers(),
                )
        except Exception:
            return []
        return []

    async def scrape_channel_page(self, channel_handle: str) -> dict[str, Any]:
        return {
            "channel_id": channel_handle if channel_handle.startswith("UC") else "",
            "title": "",
            "description": "",
            "subscriber_count": 0,
            "video_count": 0,
            "view_count": 0,
            "country": "",
            "thumbnail_url": "",
        }

    async def scrape_video_page(self, video_id: str) -> dict[str, Any]:
        return {
            "video_id": video_id,
            "title": "",
            "description": "",
            "published_at": None,
            "duration": 0,
            "view_count": 0,
            "like_count": 0,
            "comment_count": 0,
            "thumbnail_url": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
        }


class YouTubeDataAPI:
    def __init__(self) -> None:
        self._settings = settings
        self._client = YouTubeAPIClient()
        self._scraper = FallbackScraper()
        self.enable_api = bool(self._client._api_keys)

    async def search_channels(self, query: str, max_results: int = 50) -> list[dict[str, Any]]:
        try:
            data = await self._api_request("search", {"part": "snippet", "q": query, "type": "channel", "maxResults": min(max_results, 50)})
            return [
                {
                    "channel_id": item.get("snippet", {}).get("channelId", ""),
                    "title": item.get("snippet", {}).get("channelTitle", ""),
                    "description": item.get("snippet", {}).get("description", ""),
                    "thumbnail_url": "",
                }
                for item in data.get("items", [])
            ]
        except Exception:
            return await self._scraper.search_channels_fallback(query, max_results)

    async def get_channel_stats(self, channel_id: str) -> dict[str, Any]:
        try:
            data = await self._api_request("channels", {"part": "statistics,snippet", "id": channel_id})
            items = data.get("items", [])
            if not items:
                return await self._scraper.scrape_channel_page(channel_id)
            item = items[0]
            return {
                "channel_id": channel_id,
                "title": item.get("snippet", {}).get("title", ""),
                "description": item.get("snippet", {}).get("description", ""),
                "subscriber_count": int(item.get("statistics", {}).get("subscriberCount", 0) or 0),
                "video_count": int(item.get("statistics", {}).get("videoCount", 0) or 0),
                "view_count": int(item.get("statistics", {}).get("viewCount", 0) or 0),
                "country": item.get("snippet", {}).get("country", ""),
                "thumbnail_url": "",
            }
        except Exception:
            return await self._scraper.scrape_channel_page(channel_id)

    async def get_recent_videos(self, channel_id: str, max_results: int = 50) -> list[dict[str, Any]]:
        try:
            data = await self._api_request("search", {"part": "snippet", "channelId": channel_id, "type": "video", "order": "date", "maxResults": min(max_results, 50)})
            return [
                {
                    "video_id": item.get("id", {}).get("videoId", ""),
                    "title": item.get("snippet", {}).get("title", ""),
                    "description": item.get("snippet", {}).get("description", ""),
                    "published_at": self._parse_datetime(item.get("snippet", {}).get("publishedAt", "")),
                    "thumbnail_url": "",
                }
                for item in data.get("items", []) if item.get("id", {}).get("videoId", "")
            ]
        except Exception:
            return []

    async def get_video_stats(self, video_id_list: list[str]) -> list[dict[str, Any]]:
        if not video_id_list:
            return []
        try:
            data = await self._api_request("videos", {"part": "statistics,snippet,contentDetails", "id": ",".join(video_id_list[:50])})
            results = []
            for item in data.get("items", []):
                results.append({
                    "video_id": item.get("id", ""),
                    "title": item.get("snippet", {}).get("title", ""),
                    "description": item.get("snippet", {}).get("description", ""),
                    "published_at": self._parse_datetime(item.get("snippet", {}).get("publishedAt", "")),
                    "duration": self._parse_duration(item.get("contentDetails", {}).get("duration", "")),
                    "view_count": int(item.get("statistics", {}).get("viewCount", 0) or 0),
                    "like_count": int(item.get("statistics", {}).get("likeCount", 0) or 0),
                    "comment_count": int(item.get("statistics", {}).get("commentCount", 0) or 0),
                    "thumbnail_url": "",
                })
            return results
        except Exception:
            return []

    async def _api_request(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        if not self._client._api_keys:
            raise RuntimeError("API key not configured")
        from googleapiclient.discovery import build
        import httplib2

        http = httplib2.Http(timeout=10)
        key = self._client._api_keys[self._client._current_key_index]
        youtube = build("youtube", "v3", developerKey=key, http=http, cache_discovery=False)
        request = getattr(youtube, endpoint)()
        request = request.list(**params)
        return request.execute()

    @staticmethod
    def _parse_datetime(value: str) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            return None

    @staticmethod
    def _parse_duration(iso_duration: str) -> int:
        if not iso_duration:
            return 0
        total = 0
        for regex, multiplier in ((r"(\d+)H", 3600), (r"(\d+)M", 60), (r"(\d+)S", 1)):
            match = re.search(regex, iso_duration)
            if match:
                total += int(match.group(1)) * multiplier
        return total


__all__ = [
    "EndpointCost",
    "QuotaManager",
    "KeyPoolManager",
    "YouTubeAPIClient",
    "VideoMetadata",
    "YTDLPMetaExtractor",
    "AsyncYTDLPMetaExtractor",
    "DualTrackExtractor",
    "FallbackScraper",
    "YouTubeDataAPI",
    "is_proxy_reachable",
    "get_blocking_executor",
    "close_youtube_executor",
]
