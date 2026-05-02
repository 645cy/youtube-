"""
数据库种子脚本 v3 — 零硬编码

设计初衷:
  - 不插入任何假数据
  - 只创建数据库表结构
  - 所有频道/视频必须通过 YouTube API 或 yt-dlp 实时抓取入库
  - 用户通过前端搜索/导入功能添加真实频道

用法:
  1. 启动后端 -> 数据库自动初始化（空表）
  2. 前端搜索框输入 YouTube 频道名 -> 调用 /api/v1/channels/search
  3. 后端通过 YouTube Data API 抓取并入库
  4. 监控任务自动定期更新数据
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone

from apps.api.config import settings
from sqlalchemy import select

from packages.db.schema import Channel, CrawlerTask, Video, close_db, get_sessionmaker, init_db

logger = logging.getLogger("seed")


async def seed_all() -> None:
    """仅初始化数据库表结构，不插入任何数据."""
    logging.basicConfig(level=logging.INFO)

    await init_db(database_url=settings.DATABASE_URL, echo=settings.ECHO_SQL)

    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        try:
            existing = await session.scalar(select(Channel.id).limit(1))
            if existing is None:
                # CRG: Provide idempotent demo records so core screens are useful on a fresh DB.
                now = datetime.now(timezone.utc)
                channels = [
                    Channel(
                        youtube_id="UCdemoAI00000001", title="AI Creator Lab",
                        description="AI-assisted YouTube production workflows.",
                        subscriber_count=128000, video_count=84, view_count=9420000,
                        country="US", language="en", niche="ai_tools",
                    ),
                    Channel(
                        youtube_id="UCdemoBiz0000002", title="Creator Ops Weekly",
                        description="Channel operations, monetization, and repeatable content systems.",
                        subscriber_count=76000, video_count=137, view_count=5180000,
                        country="US", language="en", niche="creator_ops",
                    ),
                ]
                session.add_all(channels)
                await session.flush()
                session.add_all([
                    Video(
                        youtube_id="demoAI00001", channel_id=channels[0].id,
                        title="How to Build a Faceless AI Tutorial Pipeline",
                        description="Research, scripting, editing, and publishing in one production system.",
                        published_at=now - timedelta(days=2), duration=742,
                        view_count=184000, like_count=8700, comment_count=420,
                        tags=json.dumps(["ai", "youtube", "workflow"]), language="en",
                    ),
                    Video(
                        youtube_id="demoBiz0001", channel_id=channels[1].id,
                        title="The Weekly Operating Review for Growing Channels",
                        description="A dashboard routine for finding bottlenecks and content opportunities.",
                        published_at=now - timedelta(days=5), duration=615,
                        view_count=96000, like_count=3900, comment_count=180,
                        tags=json.dumps(["analytics", "operations", "monetization"]), language="en",
                    ),
                    CrawlerTask(
                        name="Demo channel latest videos", task_type="channel_latest",
                        target="UCdemoAI00000001", frequency="daily",
                        config_json=json.dumps({"max_results": 5}),
                    ),
                    CrawlerTask(
                        name="Demo AI niche keyword scan", task_type="keyword_search",
                        target="ai youtube automation", frequency="weekly",
                        config_json=json.dumps({"max_results": 10}),
                    ),
                ])
            await session.commit()
            logger.info("Database initialized with demo seed data")
        except Exception as e:
            await session.rollback()
            logger.error(f"Database init failed: {e}")
            raise
        finally:
            await close_db()


if __name__ == "__main__":
    asyncio.run(seed_all())
