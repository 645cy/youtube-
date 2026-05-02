r"""
批量导入真实高价值频道 — AI/变现/副业领域

用法 (在本机运行):
    cd D:\Projects\YouTube\tubefactory-ocp
    $env:PYTHONPATH="D:\Projects\YouTube\tubefactory-ocp"
    # 必填: 在 .env 或环境变量中配置 YOUTUBE_API_KEY
    # 可选: IMPORT_BASE_URL (默认 http://127.0.0.1:8000/api/v1)
    python apps\api\seed\import_trending.py

功能:
  1. 用 YouTube Data API 搜索关键词 (AI变现/副业/被动收入)
  2. 提取视频对应的频道 ID
  3. 调用后端 API 批量导入频道 + 最新视频
  4. 自动给频道打上 niche 标签

搜索策略:
  - 优先找"低粉爆款"特征的视频 (观看高但频道订阅相对低)
  - 覆盖 AI工具/副业变现/联盟营销/数字产品 四个方向
"""
from __future__ import annotations

import asyncio
import logging

import os

import httpx

from apps.api.config import settings

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("import_trending")

IMPORT_HOST = os.getenv("IMPORT_HOST", "http://127.0.0.1:8000").rstrip("/")
IMPORT_API_PREFIX = os.getenv("IMPORT_API_PREFIX", settings.API_PREFIX).rstrip("/")
BASE_URL = os.getenv("IMPORT_BASE_URL", f"{IMPORT_HOST}{IMPORT_API_PREFIX}").rstrip("/")
YOUTUBE_API_KEY = settings.YOUTUBE_API_KEY or os.getenv("YOUTUBE_API_KEY", "")

# 搜索关键词列表 — 每个对应一个变现方向
SEARCH_QUERIES: list[dict[str, str]] = [
    {"q": "AI make money 2024", "niche": "ai_monetization"},
    {"q": "AI side hustle", "niche": "ai_monetization"},
    {"q": "passive income online", "niche": "passive_income"},
    {"q": "affiliate marketing tutorial", "niche": "affiliate"},
    {"q": "YouTube automation", "niche": "youtube_automation"},
    {"q": "digital products", "niche": "digital_products"},
    {"q": "ChatGPT business", "niche": "ai_monetization"},
    {"q": "faceless YouTube channel", "niche": "youtube_automation"},
]


def youtube_search(query: str, max_results: int = 5) -> list[dict]:
    """用 YouTube Data API 搜索视频."""
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "order": "viewCount",  # 按观看数排序，找爆款
        "key": YOUTUBE_API_KEY,
    }
    try:
        resp = httpx.get(url, params=params, timeout=15)
        data = resp.json()
        return data.get("items", [])
    except Exception as e:
        logger.error(f"YouTube search failed for '{query}': {e}")
        raise RuntimeError(f"YouTube search failed for '{query}': {e}") from e


def get_channel_details(youtube_id: str) -> dict | None:
    """获取频道详情."""
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "part": "statistics,snippet",
        "id": youtube_id,
        "key": YOUTUBE_API_KEY,
    }
    try:
        resp = httpx.get(url, params=params, timeout=15)
        data = resp.json()
        items = data.get("items", [])
        return items[0] if items else None
    except Exception as e:
        logger.error(f"Channel detail failed for {youtube_id}: {e}")
        raise RuntimeError(f"Channel detail failed for {youtube_id}: {e}") from e


def get_channel_videos(youtube_id: str, max_results: int = 10) -> list[dict]:
    """获取频道最新视频."""
    # 先获取 uploads 播放列表 ID
    detail = get_channel_details(youtube_id)
    if not detail:
        return []

    uploads_id = detail.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads", "")
    if not uploads_id:
        # 手动构造 uploads playlist ID
        uploads_id = f"UU{youtube_id[2:]}" if youtube_id.startswith("UC") else ""

    if not uploads_id:
        return []

    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        "part": "snippet",
        "playlistId": uploads_id,
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY,
    }
    try:
        resp = httpx.get(url, params=params, timeout=15)
        data = resp.json()
        return data.get("items", [])
    except Exception as e:
        logger.error(f"Video list failed for {youtube_id}: {e}")
        raise RuntimeError(f"Video list failed for {youtube_id}: {e}") from e


def get_video_stats(video_ids: list[str]) -> list[dict]:
    """批量获取视频统计."""
    if not video_ids:
        return []
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "statistics,contentDetails,snippet",
        "id": ",".join(video_ids),
        "key": YOUTUBE_API_KEY,
    }
    try:
        resp = httpx.get(url, params=params, timeout=15)
        data = resp.json()
        return data.get("items", [])
    except Exception as e:
        logger.error(f"Video stats failed: {e}")
        raise RuntimeError(f"Video stats failed: {e}") from e


async def import_channel(youtube_id: str, niche: str) -> dict | None:
    """通过后端 API 导入频道."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{BASE_URL}/channels/import-youtube",
                params={"youtube_id": youtube_id},
            )
            if resp.status_code == 409:
                logger.info(f"  ⚠️  频道已存在: {youtube_id}")
                # 尝试获取已存在的频道
                list_resp = await client.get(f"{BASE_URL}/channels", params={"limit": 200})
                data = list_resp.json()
                for item in data.get("items", []):
                    if item.get("youtube_id") == youtube_id:
                        return item
                return None
            if resp.status_code == 201:
                channel = resp.json()
                # 更新 niche 标签
                await client.put(
                    f"{BASE_URL}/channels/{channel['id']}",
                    json={"niche": niche},
                )
                return channel
            logger.warning(f"  ❌ 导入失败 HTTP {resp.status_code}: {resp.text[:100]}")
            return None
    except Exception as e:
        logger.error(f"  ❌ 导入异常: {e}")
        raise RuntimeError(f"Import failed for {youtube_id}: {e}") from e


async def import_videos_for_channel(channel_id: int, youtube_id: str, niche: str) -> int:
    """导入频道最新视频."""
    items = get_channel_videos(youtube_id, max_results=10)
    if not items:
        return 0

    video_ids = []
    video_data = {}
    for item in items:
        snippet = item.get("snippet", {})
        vid = snippet.get("resourceId", {}).get("videoId", "")
        if vid:
            video_ids.append(vid)
            video_data[vid] = {
                "title": snippet.get("title", ""),
                "description": snippet.get("description", ""),
                "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url"),
                "published_at": snippet.get("publishedAt"),
            }
    # 获取统计
    stats = get_video_stats(video_ids)
    imported = 0

    async with httpx.AsyncClient(timeout=15) as client:
        for item in stats:
            vid = item.get("id", "")
            snippet = item.get("snippet", {})
            statistics = item.get("statistics", {})
            cd = item.get("contentDetails", {})

            # 解析时长
            duration_str = cd.get("duration", "")
            duration_sec = None
            if duration_str:
                import re
                m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration_str)
                if m:
                    duration_sec = (int(m.group(1) or 0) * 3600 +
                                   int(m.group(2) or 0) * 60 +
                                   int(m.group(3) or 0))

            video_body = {
                "youtube_id": vid,
                "channel_id": channel_id,
                "title": snippet.get("title", video_data.get(vid, {}).get("title", "Unknown")),
                "description": snippet.get("description", video_data.get(vid, {}).get("description", "")),
                "thumbnail_url": (
                    snippet.get("thumbnails", {}).get("high", {}).get("url")
                    or video_data.get(vid, {}).get("thumbnail_url")
                ),
                "published_at": video_data.get(vid, {}).get("published_at"),
                "duration": duration_sec,
                "view_count": int(statistics.get("viewCount", 0)) if statistics.get("viewCount") else None,
                "like_count": int(statistics.get("likeCount", 0)) if statistics.get("likeCount") else None,
                "comment_count": int(statistics.get("commentCount", 0)) if statistics.get("commentCount") else None,
                "is_short": duration_sec is not None and duration_sec <= 60,
            }

            try:
                resp = await client.post(f"{BASE_URL}/videos", json=video_body)
                if resp.status_code in (201, 409):
                    imported += 1
            except Exception as e:
                logger.warning(f"    Video import failed {vid}: {e}")

    return imported


async def main() -> None:
    if not YOUTUBE_API_KEY:
        logger.error("❌ 缺少 YOUTUBE_API_KEY。请在 .env 或系统环境变量中配置后重试。")
        logger.error("   示例: YOUTUBE_API_KEY=your_real_key")
        return

    logger.info("=" * 60)
    logger.info(" TubeFactory 高价值频道批量导入")
    logger.info("=" * 60)
    logger.info("")
    logger.info("搜索方向:")
    for sq in SEARCH_QUERIES:
        logger.info(f"  • {sq['q']} → {sq['niche']}")
    logger.info("")

    # 1. 搜索获取频道 ID 列表
    channel_map: dict[str, str] = {}  # youtube_id -> niche
    for sq in SEARCH_QUERIES:
        logger.info(f"🔍 搜索: {sq['q']}")
        items = youtube_search(sq["q"], max_results=3)
        for item in items:
            snippet = item.get("snippet", {})
            channel_id = snippet.get("channelId", "")
            title = snippet.get("channelTitle", "Unknown")
            if channel_id and channel_id not in channel_map:
                channel_map[channel_id] = sq["niche"]
                logger.info(f"   发现频道: {title} ({channel_id})")

    logger.info(f"\n📊 共找到 {len(channel_map)} 个不重复频道")
    logger.info("")

    # 2. 逐个导入
    total_channels = 0
    total_videos = 0
    for youtube_id, niche in channel_map.items():
        detail = get_channel_details(youtube_id)
        if not detail:
            continue

        snippet = detail.get("snippet", {})
        stats = detail.get("statistics", {})
        title = snippet.get("title", "Unknown")
        subs = int(stats.get("subscriberCount", 0)) if stats.get("subscriberCount") else 0
        videos = int(stats.get("videoCount", 0)) if stats.get("videoCount") else 0
        views = int(stats.get("viewCount", 0)) if stats.get("viewCount") else 0

        logger.info(f"📥 导入: {title} ({subs:,} 订阅, {videos:,} 视频, {views:,} 观看) [{niche}]")

        channel = await import_channel(youtube_id, niche)
        if channel:
            total_channels += 1
            # 导入视频
            imported_videos = await import_videos_for_channel(channel["id"], youtube_id, niche)
            total_videos += imported_videos
            logger.info(f"   ✅ 导入 {imported_videos} 个视频")

    logger.info("")
    logger.info("=" * 60)
    logger.info(f" 导入完成: {total_channels} 个频道, {total_videos} 个视频")
    logger.info("=" * 60)
    logger.info("")
    logger.info("现在打开 Dashboard 就能看到数据了")
    logger.info("推荐下一步: 去 Lab 填画像 → Factory 选题 → Radar 看竞品")


if __name__ == "__main__":
    asyncio.run(main())
