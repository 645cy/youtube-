"""
批量导入多样化演示数据 — 20 个频道 + 60 个视频
覆盖 tech/education/finance/lifestyle/entertainment 五大领域
"""
import asyncio
from datetime import datetime, timezone
from sqlalchemy import select
from apps.api.config import settings
from packages.db.schema import (
    get_engine, get_sessionmaker,
    Channel, Video, MetricHistory, MetricType,
    MonitorJob, MonitorStatus, JobType,
)

CHANNELS = [
    # --- tech (AI/编程) ---
    {"youtube_id": "UCsBjURrPoezykLs9EqgamOA", "title": "Fireship", "subscriber_count": 3_300_000, "video_count": 800, "view_count": 500_000_000, "niche": "tech", "country": "US"},
    {"youtube_id": "UC9x0AN7BWHpCDHSm9NiJFJQ", "title": "NetworkChuck", "subscriber_count": 4_500_000, "video_count": 600, "view_count": 400_000_000, "niche": "tech", "country": "US"},
    {"youtube_id": "UC29ju8bIPH5as8OGnQzwJyA", "title": "Traversy Media", "subscriber_count": 2_200_000, "video_count": 1000, "view_count": 300_000_000, "niche": "tech", "country": "US"},
    {"youtube_id": "UCWv7vMbMWH4-V0ZXdmDpPBA", "title": "Programming with Mosh", "subscriber_count": 4_000_000, "video_count": 250, "view_count": 350_000_000, "niche": "tech", "country": "US"},
    {"youtube_id": "UC4JX40jDee_tINbkjycV4Sg", "title": "Tech With Tim", "subscriber_count": 1_400_000, "video_count": 700, "view_count": 150_000_000, "niche": "tech", "country": "CA"},
    {"youtube_id": "UCvjgXvBlbQiydffZU7m1_aw", "title": "The Coding Train", "subscriber_count": 1_800_000, "video_count": 1200, "view_count": 180_000_000, "niche": "tech", "country": "US"},
    {"youtube_id": "UC8butISFwT-Wi7c0vm8z5Ww", "title": "freeCodeCamp", "subscriber_count": 9_000_000, "video_count": 1500, "view_count": 600_000_000, "niche": "tech", "country": "US"},
    {"youtube_id": "UCBVCi4JbhhZUIl3P0Zww9ZQ", "title": "Liam Ottley", "subscriber_count": 180_000, "video_count": 80, "view_count": 8_000_000, "niche": "tech", "country": "US"},

    # --- education ---
    {"youtube_id": "UCX6b17PVsYBQ0ip5gyeme-Q", "title": "CrashCourse", "subscriber_count": 16_000_000, "video_count": 1400, "view_count": 2_000_000_000, "niche": "education", "country": "US"},
    {"youtube_id": "UCtYLUTtgS3k1Fg4y5tAhLbw", "title": "StatQuest", "subscriber_count": 1_200_000, "video_count": 300, "view_count": 80_000_000, "niche": "education", "country": "US"},
    {"youtube_id": "UCCezIgC97PvUuC4qJ-i-3ew", "title": "Khan Academy", "subscriber_count": 8_500_000, "video_count": 8000, "view_count": 2_500_000_000, "niche": "education", "country": "US"},

    # --- finance (理财/副业) ---
    {"youtube_id": "UCGy7SkBJCebgCFUjr1OV3hg", "title": "Graham Stephan", "subscriber_count": 5_000_000, "video_count": 1200, "view_count": 700_000_000, "niche": "finance", "country": "US"},
    {"youtube_id": "UCV6KDgJskWaEckne7aK8ktQ", "title": "Andrei Jikh", "subscriber_count": 2_500_000, "video_count": 400, "view_count": 250_000_000, "niche": "finance", "country": "US"},
    {"youtube_id": "UC7KqjJyRbfz9W5QjKJ7S8Yw", "title": "Iman Gadzhi", "subscriber_count": 5_500_000, "video_count": 300, "view_count": 400_000_000, "niche": "finance", "country": "US"},
    {"youtube_id": "UCYKRkEJ71s0Pbbo9Gz6jPBA", "title": "Joshua Mayo", "subscriber_count": 1_800_000, "video_count": 200, "view_count": 120_000_000, "niche": "finance", "country": "US"},
    {"youtube_id": "UCq4G_3Bj8uGHc1-KG4kRp3A", "title": "Dave Nick", "subscriber_count": 900_000, "video_count": 150, "view_count": 60_000_000, "niche": "finance", "country": "US"},

    # --- lifestyle ---
    {"youtube_id": "UClb90NQQcskPUGDIXsQEPEQ", "title": "Matt DAvella", "subscriber_count": 3_800_000, "video_count": 200, "view_count": 300_000_000, "niche": "lifestyle", "country": "US"},
    {"youtube_id": "UCn8zNIfYAQNdrFRrr8aoibw", "title": "MuchelleB", "subscriber_count": 600_000, "video_count": 180, "view_count": 40_000_000, "niche": "lifestyle", "country": "US"},

    # --- entertainment ---
    {"youtube_id": "UCX6OQ3DkcsbYNE6H8uQQuVA", "title": "MrBeast", "subscriber_count": 350_000_000, "video_count": 800, "view_count": 60_000_000_000, "niche": "entertainment", "country": "US"},
    {"youtube_id": "UC-lHJZR3Gqxm24_Vd_AJ5Yw", "title": "PewDiePie", "subscriber_count": 111_000_000, "video_count": 4700, "view_count": 29_000_000_000, "niche": "entertainment", "country": "US"},
    {"youtube_id": "UCpEhnqL0y41EpW2TvWAHD7Q", "title": "SSSniperWolf", "subscriber_count": 34_000_000, "video_count": 3000, "view_count": 15_000_000_000, "niche": "entertainment", "country": "US"},
]

VIDEOS = [
    # Fireship style: short explainers
    {"youtube_id": "q6EoRBvdVPQ", "title": "React in 100 Seconds", "view_count": 5_000_000, "duration": 120, "is_short": False, "channel_idx": 0},
    {"youtube_id": "DHjN7dqPSIE", "title": "Web Scraping with Python", "view_count": 1_800_000, "duration": 900, "is_short": False, "channel_idx": 0},
    {"youtube_id": "Mus_vwhTCq0", "title": "JavaScript in 100 Seconds", "view_count": 3_200_000, "duration": 120, "is_short": False, "channel_idx": 0},
    {"youtube_id": "Tn6-PIqc4UM", "title": "React Hooks in 100 Seconds", "view_count": 2_100_000, "duration": 120, "is_short": False, "channel_idx": 0},

    # NetworkChuck
    {"youtube_id": "JeznW_7DlB0", "title": "Linux for Hackers", "view_count": 6_000_000, "duration": 1800, "is_short": False, "channel_idx": 1},
    {"youtube_id": "mRMmlo_Uqcs", "title": "Learn Docker in 7 Easy Steps", "view_count": 4_000_000, "duration": 900, "is_short": False, "channel_idx": 1},
    {"youtube_id": "W0TN8gE7bMg", "title": "I Built a Free AI Tool", "view_count": 1_200_000, "duration": 1200, "is_short": False, "channel_idx": 1},
    {"youtube_id": "HTPxk-Ej2-U", "title": "How I Make Money with AI", "view_count": 800_000, "duration": 1500, "is_short": False, "channel_idx": 1},

    # Traversy
    {"youtube_id": "gfkTfcpWqAY", "title": "Python Tutorial for Beginners", "view_count": 35_000_000, "duration": 2700, "is_short": False, "channel_idx": 2},
    {"youtube_id": "TlB_eWDSMt4", "title": "Node.js Tutorial for Beginners", "view_count": 15_000_000, "duration": 1800, "is_short": False, "channel_idx": 2},
    {"youtube_id": "W6NZfCO5SIk", "title": "JavaScript Tutorial for Beginners", "view_count": 12_000_000, "duration": 3600, "is_short": False, "channel_idx": 2},
    {"youtube_id": "I-k-iTUMQAY", "title": "React Course for Beginners", "view_count": 2_500_000, "duration": 4800, "is_short": False, "channel_idx": 2},

    # Mosh
    {"youtube_id": "QXeEoD0pBUC", "title": "Learn Python in 12 Minutes", "view_count": 8_000_000, "duration": 720, "is_short": False, "channel_idx": 3},
    {"youtube_id": "_uQrJ0TkZlc", "title": "Python Tutorial for Beginners", "view_count": 22_000_000, "duration": 9000, "is_short": False, "channel_idx": 3},
    {"youtube_id": "yOU6P4Cfl5A", "title": "Docker Tutorial for Beginners", "view_count": 3_500_000, "duration": 3600, "is_short": False, "channel_idx": 3},

    # Tech With Tim
    {"youtube_id": "s8XjEugrx3o", "title": "Python As Fast as Possible", "view_count": 5_500_000, "duration": 2400, "is_short": False, "channel_idx": 4},
    {"youtube_id": "dn4Xmpv0L2w", "title": "ChatGPT Full Course", "view_count": 2_800_000, "duration": 5400, "is_short": False, "channel_idx": 4},
    {"youtube_id": "GAkzxB3hfQ4", "title": "Automate with Python", "view_count": 1_500_000, "duration": 1800, "is_short": False, "channel_idx": 4},

    # Coding Train
    {"youtube_id": "nfmV2kuQKwA", "title": "Coding Challenge: Snake Game", "view_count": 2_000_000, "duration": 1800, "is_short": False, "channel_idx": 5},
    {"youtube_id": "HerCR8bw_GE", "title": "Coding Challenge: Matrix Rain", "view_count": 1_200_000, "duration": 1500, "is_short": False, "channel_idx": 5},

    # freeCodeCamp
    {"youtube_id": "pQN-pnXPaVg", "title": "Full Stack Web Dev Course", "view_count": 8_000_000, "duration": 7200, "is_short": False, "channel_idx": 6},
    {"youtube_id": "KJgsSFOSQv0", "title": "C Programming Tutorial", "view_count": 6_000_000, "duration": 14400, "is_short": False, "channel_idx": 6},
    {"youtube_id": "rfscVS0vtbw", "title": "Learn Python - Full Course", "view_count": 45_000_000, "duration": 16200, "is_short": False, "channel_idx": 6},
    {"youtube_id": "PkZNo7MFNFg", "title": "JavaScript Full Course", "view_count": 28_000_000, "duration": 14400, "is_short": False, "channel_idx": 6},

    # Liam Ottley (AI agency)
    {"youtube_id": "fHszYJUfyHE", "title": "How to Start an AI Agency", "view_count": 1_000_000, "duration": 1800, "is_short": False, "channel_idx": 7},
    {"youtube_id": "u9Wj2Z9lJ8Q", "title": "AI Automation Business Model", "view_count": 500_000, "duration": 1200, "is_short": False, "channel_idx": 7},

    # CrashCourse
    {"youtube_id": "Q6_5NdLu0fw", "title": "Computer Science Crash Course", "view_count": 5_000_000, "duration": 720, "is_short": False, "channel_idx": 8},
    {"youtube_id": "RpkQEq75y18", "title": "Artificial Intelligence Explained", "view_count": 3_000_000, "duration": 600, "is_short": False, "channel_idx": 8},

    # StatQuest
    {"youtube_id": "t4K6lney7Zw", "title": "Machine Learning in 5 Minutes", "view_count": 2_000_000, "duration": 300, "is_short": False, "channel_idx": 9},
    {"youtube_id": "aircAruvnKk", "title": "Neural Networks Explained", "view_count": 8_000_000, "duration": 1200, "is_short": False, "channel_idx": 9},

    # Khan Academy
    {"youtube_id": "8ENUbI9opZw", "title": "Introduction to Algebra", "view_count": 4_000_000, "duration": 900, "is_short": False, "channel_idx": 10},

    # Graham Stephan
    {"youtube_id": "gWzQSBohK3Q", "title": "How I Became a Millionaire", "view_count": 10_000_000, "duration": 1200, "is_short": False, "channel_idx": 11},
    {"youtube_id": "N1S7CwjOI1w", "title": "How to Invest for Beginners", "view_count": 8_000_000, "duration": 1800, "is_short": False, "channel_idx": 11},
    {"youtube_id": "4j2emMn7UaI", "title": "Passive Income Ideas", "view_count": 6_000_000, "duration": 1500, "is_short": False, "channel_idx": 11},
    {"youtube_id": "9QEK7F8pX2I", "title": "How I Save 99% of My Income", "view_count": 5_000_000, "duration": 1200, "is_short": False, "channel_idx": 11},

    # Andrei Jikh
    {"youtube_id": "kD5yc1L6rpI", "title": "How to Invest in Stocks", "view_count": 5_000_000, "duration": 1800, "is_short": False, "channel_idx": 12},
    {"youtube_id": "rE4xL08dHd4", "title": "My Dividend Portfolio", "view_count": 2_500_000, "duration": 1200, "is_short": False, "channel_idx": 12},

    # Iman Gadzhi
    {"youtube_id": "5MgBikgcWnY", "title": "How I Started My Business", "view_count": 8_000_000, "duration": 1500, "is_short": False, "channel_idx": 13},
    {"youtube_id": "5MgBikgcWnY", "title": "The Truth About Making Money Online", "view_count": 4_000_000, "duration": 1200, "is_short": False, "channel_idx": 13},
    {"youtube_id": "qK0crPLQcSw", "title": "YouTube Automation Tutorial", "view_count": 3_000_000, "duration": 1200, "is_short": False, "channel_idx": 13},

    # Joshua Mayo
    {"youtube_id": "KpL6uQeX2Aw", "title": "7 Passive Income Streams", "view_count": 3_000_000, "duration": 900, "is_short": False, "channel_idx": 14},
    {"youtube_id": "5n1p7zK-1jE", "title": "How to Make Money with YouTube", "view_count": 2_000_000, "duration": 1200, "is_short": False, "channel_idx": 14},

    # Dave Nick
    {"youtube_id": "KkC2b5x7e2U", "title": "YouTube Automation Full Guide", "view_count": 1_500_000, "duration": 1800, "is_short": False, "channel_idx": 15},
    {"youtube_id": "8nM3wU8lV6Q", "title": "How to Make $1000/Month Online", "view_count": 1_000_000, "duration": 1500, "is_short": False, "channel_idx": 15},

    # Matt D'Avella
    {"youtube_id": "sJ7l2zE8Q1g", "title": "The Minimalist Lifestyle", "view_count": 5_000_000, "duration": 600, "is_short": False, "channel_idx": 16},
    {"youtube_id": "9QEK7F8pX2I", "title": "I Tried Minimalism for 30 Days", "view_count": 8_000_000, "duration": 900, "is_short": False, "channel_idx": 16},

    # MuchelleB
    {"youtube_id": "7nH1q8J3-0k", "title": "How to Build Habits That Stick", "view_count": 2_000_000, "duration": 600, "is_short": False, "channel_idx": 17},

    # MrBeast
    {"youtube_id": "J_z-W4UVhkw", "title": "I Survived 50 Hours in Antarctica", "view_count": 200_000_000, "duration": 900, "is_short": False, "channel_idx": 18},
    {"youtube_id": "kX3nB4P4m5s", "title": "$1 vs $1,000,000 Hotel Room", "view_count": 350_000_000, "duration": 1200, "is_short": False, "channel_idx": 18},
    {"youtube_id": "hD6A9_2L0kQ", "title": "I Built 100 Houses for Homeless", "view_count": 150_000_000, "duration": 900, "is_short": False, "channel_idx": 18},
    {"youtube_id": "hD6A9_2L0kQ2", "title": "Last to Leave Circle Wins $500,000", "view_count": 280_000_000, "duration": 1500, "is_short": False, "channel_idx": 18},

    # PewDiePie
    {"youtube_id": "6Dh-RL__uN4", "title": "bitch lasagna", "view_count": 300_000_000, "duration": 120, "is_short": False, "channel_idx": 19},
    {"youtube_id": "6_51mJ8mE6c", "title": "Congratulations", "view_count": 250_000_000, "duration": 240, "is_short": False, "channel_idx": 19},

    # SSSniperWolf
    {"youtube_id": "5iHeYqD1nNY", "title": "Reacting to My Old Videos", "view_count": 20_000_000, "duration": 600, "is_short": False, "channel_idx": 20},
]


async def main():
    get_engine(database_url=settings.DATABASE_URL)
    sm = get_sessionmaker()
    async with sm() as session:
        now = datetime.now(timezone.utc)
        ch_ids = []
        inserted_channels = 0
        inserted_videos = 0

        for data in CHANNELS:
            existing = await session.execute(
                select(Channel).where(Channel.youtube_id == data["youtube_id"])
            )
            if existing.scalar_one_or_none():
                continue

            ch = Channel(
                youtube_id=data["youtube_id"],
                title=data["title"],
                description="",
                subscriber_count=data["subscriber_count"],
                video_count=data["video_count"],
                view_count=data["view_count"],
                niche=data.get("niche"),
                country=data.get("country"),
            )
            session.add(ch)
            await session.flush()
            ch_ids.append(ch.id)
            inserted_channels += 1

            # metric_history
            session.add(MetricHistory(
                channel_id=ch.id, metric_type=MetricType.SUBSCRIBER,
                value=float(data["subscriber_count"]), recorded_at=now
            ))
            session.add(MetricHistory(
                channel_id=ch.id, metric_type=MetricType.VIEW,
                value=float(data["view_count"]), recorded_at=now
            ))

            # monitor_jobs
            session.add(MonitorJob(
                channel_id=ch.id,
                job_type=JobType.STATS,
                frequency="daily",
                status=MonitorStatus.ACTIVE,
                last_run_at=now,
                next_run_at=now,
            ))
            session.add(MonitorJob(
                channel_id=ch.id,
                job_type=JobType.NEW_VIDEOS,
                frequency="daily",
                status=MonitorStatus.ACTIVE,
                last_run_at=now,
                next_run_at=now,
            ))

            print(f"  + {data['title']} ({data['subscriber_count']:,} subs) [{data.get('niche','')}]")

        for vdata in VIDEOS:
            idx = vdata.pop("channel_idx")
            if idx >= len(ch_ids):
                continue
            ch_id = ch_ids[idx]

            existing = await session.execute(
                select(Video).where(Video.youtube_id == vdata["youtube_id"])
            )
            if existing.scalar_one_or_none():
                continue

            try:
                video = Video(channel_id=ch_id, **vdata)
                session.add(video)
                await session.flush()
                inserted_videos += 1
            except Exception:
                await session.rollback()
                # 重新开启事务上下文
                pass

        await session.commit()
        print(f"\nDone: {inserted_channels} channels, {inserted_videos} videos, {inserted_channels*2} monitor jobs")


if __name__ == "__main__":
    asyncio.run(main())
