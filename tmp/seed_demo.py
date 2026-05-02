"""
插入演示数据 — 5 个真实技术频道 + 10 个爆款视频
沙盒可用，无需网络
"""
import asyncio
from datetime import datetime, timezone
from sqlalchemy import select
from apps.api.config import settings
from packages.db.schema import get_engine, get_sessionmaker, Channel, Video, MetricHistory, MetricType

SEED_CHANNELS = [
    {
        "youtube_id": "UCsBjURrPoezykLs9EqgamOA",
        "title": "Fireship",
        "description": "High-intensity code tutorials and tech explainers. Known for 100-second explainers that go viral.",
        "subscriber_count": 3_300_000,
        "video_count": 800,
        "view_count": 500_000_000,
        "thumbnail_url": "https://yt3.ggpht.com/ytc/AIdro_k3c6E-S4zq5cL8vBQ3F-0c0_mQ_CyD5vH5J2gqfw=s88-c-k-c0x00ffffff-no-rj",
        "niche": "tech",
    },
    {
        "youtube_id": "UC9x0AN7BWHpCDHSm9NiJFJQ",
        "title": "NetworkChuck",
        "description": "IT, Cyber Security, and making money with tech. Massive growth from zero to millions.",
        "subscriber_count": 4_500_000,
        "video_count": 600,
        "view_count": 400_000_000,
        "thumbnail_url": "https://yt3.ggpht.com/ytc/AIdro_lC8t-P1mT-c7R8ePQXKYCzS6jO9g3M3GzRhG_6lw=s88-c-k-c0x00ffffff-no-rj",
        "niche": "tech",
    },
    {
        "youtube_id": "UC29ju8bIPH5as8OGnQzwJyA",
        "title": "Traversy Media",
        "description": "Web development and programming tutorials. One of the original coding YouTubers.",
        "subscriber_count": 2_200_000,
        "video_count": 1000,
        "view_count": 300_000_000,
        "thumbnail_url": "https://yt3.ggpht.com/ytc/AIdro_k5uqC40P_clip_s88-c-k-c0x00ffffff-no-rj",
        "niche": "tech",
    },
    {
        "youtube_id": "UCWv7vMbMWH4-V0ZXdmDpPBA",
        "title": "Programming with Mosh",
        "description": "Professional software engineering training. Clean tutorials with high production value.",
        "subscriber_count": 4_000_000,
        "video_count": 250,
        "view_count": 350_000_000,
        "thumbnail_url": "https://yt3.ggpht.com/ytc/AIdro_nHKGl-pK1_8-5su4m_Ar0g0n8GYzP-3GfDn9K6rQ=s88-c-k-c0x00ffffff-no-rj",
        "niche": "education",
    },
    {
        "youtube_id": "UC4JX40jDee_tINbkjycV4Sg",
        "title": "Tech With Tim",
        "description": "Python tutorials, tech reviews, and coding projects. Started as a teenager, now a massive channel.",
        "subscriber_count": 1_400_000,
        "video_count": 700,
        "view_count": 150_000_000,
        "thumbnail_url": "https://yt3.ggpht.com/ytc/AIdro_l-PVXxU2gPmj8M00K9k-NNz6_8aZxGz-sO8kV4wA=s88-c-k-c0x00ffffff-no-rj",
        "niche": "tech",
    },
]

SEED_VIDEOS = [
    {"youtube_id": "gfkTfcpWqAY", "title": "Python Tutorial for Beginners", "view_count": 35_000_000, "duration": 2700, "is_short": False},
    {"youtube_id": "TlB_eWDSMt4", "title": "Node.js Tutorial for Beginners", "view_count": 15_000_000, "duration": 1800, "is_short": False},
    {"youtube_id": "W6NZfCO5SIk", "title": "JavaScript Tutorial for Beginners", "view_count": 12_000_000, "duration": 3600, "is_short": False},
    {"youtube_id": "QXeEoD0pBUC", "title": "Learn Python in 12 Minutes", "view_count": 8_000_000, "duration": 720, "is_short": False},
    {"youtube_id": "JeznW_7DlB0", "title": "Linux for Hackers - NetworkChuck", "view_count": 6_000_000, "duration": 1500, "is_short": False},
    {"youtube_id": "q6EoRBvdVPQ", "title": "Y# Code in 100 Seconds - Fireship", "view_count": 5_000_000, "duration": 120, "is_short": False},
    {"youtube_id": "mRMmlo_Uqcs", "title": "Learn Docker in 7 Easy Steps", "view_count": 4_000_000, "duration": 900, "is_short": False},
    {"youtube_id": "qK0crPLQcSw", "title": "How to Start a YouTube Channel", "view_count": 3_000_000, "duration": 1200, "is_short": False},
    {"youtube_id": "I-k-iTUMQAY", "title": "React Course for Beginners", "view_count": 2_500_000, "duration": 4800, "is_short": False},
    {"youtube_id": "DHjN7dqPSIE", "title": "Web Scraping with Python", "view_count": 1_800_000, "duration": 1800, "is_short": False},
]


async def main():
    get_engine(database_url=settings.DATABASE_URL)
    sm = get_sessionmaker()
    async with sm() as session:
        now = datetime.now(timezone.utc)
        ch_ids = []

        for data in SEED_CHANNELS:
            existing = await session.execute(
                select(Channel).where(Channel.youtube_id == data["youtube_id"])
            )
            if existing.scalar_one_or_none():
                print(f"Skip existing: {data['title']}")
                continue

            ch = Channel(**data)
            session.add(ch)
            await session.flush()
            ch_ids.append(ch.id)

            session.add(MetricHistory(
                channel_id=ch.id, metric_type=MetricType.SUBSCRIBER,
                value=float(data["subscriber_count"]), recorded_at=now
            ))
            session.add(MetricHistory(
                channel_id=ch.id, metric_type=MetricType.VIEW,
                value=float(data["view_count"]), recorded_at=now
            ))
            print(f"Inserted: {data['title']} id={ch.id}")

        for i, vdata in enumerate(SEED_VIDEOS):
            if not ch_ids:
                break
            ch_id = ch_ids[i % len(ch_ids)]
            existing = await session.execute(
                select(Video).where(Video.youtube_id == vdata["youtube_id"])
            )
            if existing.scalar_one_or_none():
                continue

            video = Video(channel_id=ch_id, **vdata)
            session.add(video)
            print(f"  Video: {vdata['title'][:40]}... views={vdata['view_count']:,}")

        await session.commit()
        print("\nDone. 刷新 Dashboard 看数据。")


if __name__ == "__main__":
    asyncio.run(main())
