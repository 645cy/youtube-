import sys
import os

sys.path.insert(0, r"D:\Projects\YouTube\tubefactory-ocp")
sys.path.insert(0, r"D:\Projects\YouTube\tubefactory-ocp\apps\api")
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///D:/Projects/YouTube/tubefactory-ocp/data/tubefactory.db"

from packages.db.schema import get_sessionmaker, Channel
from sqlalchemy import select, desc, func
import asyncio


async def main():
    sm = get_sessionmaker()
    async with sm() as session:
        # 高均播频道
        result = await session.execute(
            select(Channel)
            .where(Channel.video_count > 0, Channel.view_count > 0)
            .order_by(desc(Channel.view_count / Channel.video_count))
            .limit(20)
        )
        items = result.scalars().all()
        print("===== TOP 20 高均播 AI 频道 =====\n")
        print(f"{'排名':>4} {'均播':>12} {'订阅':>10} {'视频':>6} {'频道名':<45}")
        print("-" * 90)
        for i, ch in enumerate(items, 1):
            avg = (ch.view_count or 0) // max(ch.video_count or 0, 1)
            subs = ch.subscriber_count or 0
            vids = ch.video_count or 0
            title = (ch.title or "")[:43]
            print(f"{i:>4} {avg:>12,} {subs:>10,} {vids:>6,} {title:<45}")

        # 订阅数分布
        print("\n===== 频道订阅数分布 =====\n")
        ranges = [
            (0, 1000, "<1K"),
            (1000, 10000, "1K-10K"),
            (10000, 100000, "10K-100K"),
            (100000, 1000000, "100K-1M"),
            (1000000, 10000000, "1M-10M"),
            (10000000, 999999999999, ">10M"),
        ]
        for lo, hi, label in ranges:
            cnt = await session.scalar(
                select(func.count()).select_from(Channel)
                .where(Channel.subscriber_count >= lo, Channel.subscriber_count < hi)
            )
            print(f"  {label:>10}: {cnt:>5,} 个频道")

        # 有评分 vs 无评分
        scored = await session.scalar(
            select(func.count()).select_from(Channel).where(Channel.discovery_score > 0)
        )
        unscored = await session.scalar(
            select(func.count()).select_from(Channel).where(
                (Channel.discovery_score == None) | (Channel.discovery_score == 0)
            )
        )
        print(f"\n  有评分: {scored:,}")
        print(f"  无评分: {unscored:,}")


asyncio.run(main())
