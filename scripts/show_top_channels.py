import sys
import os

sys.path.insert(0, r"D:\Projects\YouTube\tubefactory-ocp")
sys.path.insert(0, r"D:\Projects\YouTube\tubefactory-ocp\apps\api")
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///D:/Projects/YouTube/tubefactory-ocp/data/tubefactory.db"

from packages.db.schema import get_sessionmaker, Channel
from sqlalchemy import select, desc
import asyncio


async def top_channels():
    sm = get_sessionmaker()
    async with sm() as session:
        # 按 discovery_score 排序，没有的话按 subscriber_count 排序
        result = await session.execute(
            select(Channel)
            .order_by(desc(Channel.discovery_score))
            .limit(30)
        )
        items = result.scalars().all()

        print("===== TOP 30 AI 频道（按 discovery_score）=====\n")
        print(f"{'排名':>4} {'评分':>6} {'订阅':>10} {'均播':>10} {'视频':>6} {'频道名':<40} {'YouTube ID':<30}")
        print("-" * 120)
        for i, ch in enumerate(items, 1):
            subs = ch.subscriber_count or 0
            views = ch.view_count or 0
            vids = ch.video_count or 0
            avg = views // max(vids, 1)
            title = (ch.title or "")[:38]
            cid = ch.youtube_id or ""
            score = ch.discovery_score or 0.0
            print(f"{i:>4} {score:>6.1f} {subs:>10,} {avg:>10,} {vids:>6,} {title:<40} {cid:<30}")

        # 也显示按订阅数排序的
        print("\n===== TOP 20 AI 频道（按订阅数）=====\n")
        result2 = await session.execute(
            select(Channel)
            .order_by(desc(Channel.subscriber_count))
            .limit(20)
        )
        items2 = result2.scalars().all()
        print(f"{'排名':>4} {'订阅':>12} {'视频':>6} {'均播':>10} {'频道名':<45}")
        print("-" * 90)
        for i, ch in enumerate(items2, 1):
            subs = ch.subscriber_count or 0
            views = ch.view_count or 0
            vids = ch.video_count or 0
            avg = views // max(vids, 1)
            title = (ch.title or "")[:43]
            print(f"{i:>4} {subs:>12,} {vids:>6,} {avg:>10,} {title:<45}")


asyncio.run(top_channels())
