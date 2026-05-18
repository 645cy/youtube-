from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select  # noqa: E402

from apps.api.config import settings  # noqa: E402
from packages.db.schema import Channel, close_db, get_sessionmaker, init_db  # noqa: E402


DEMO_CHANNEL_TITLES = {
    "The Coding Train",
    "Fireship",
    "NetworkChuck",
    "Traversy Media",
    "Programming with Mosh",
    "Tech With Tim",
    "freeCodeCamp",
    "Liam Ottley",
    "CrashCourse",
    "StatQuest",
    "Khan Academy",
    "Graham Stephan",
    "Andrei Jikh",
    "Iman Gadzhi",
    "Joshua Mayo",
    "Dave Nick",
    "Matt DAvella",
    "MuchelleB",
    "MrBeast",
    "PewDiePie",
    "SSSniperWolf",
}


async def cleanup_demo_data(dry_run: bool = True) -> dict[str, object]:
    await init_db(database_url=settings.DATABASE_URL, echo=settings.ECHO_SQL)
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        result = await session.execute(select(Channel).where(Channel.title.in_(DEMO_CHANNEL_TITLES)))
        channels = list(result.scalars().all())
        payload = {
            "dry_run": dry_run,
            "matched_count": len(channels),
            "channels": [
                {
                    "id": channel.id,
                    "youtube_id": channel.youtube_id,
                    "title": channel.title,
                    "subscriber_count": channel.subscriber_count,
                    "video_count": channel.video_count,
                    "view_count": channel.view_count,
                    "created_at": channel.created_at.isoformat() if channel.created_at else None,
                }
                for channel in channels
            ],
        }
        if not dry_run:
            for channel in channels:
                await session.delete(channel)
            await session.commit()
        await close_db()
        return payload


async def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Remove old TubeFactory demo channels.")
    parser.add_argument("--apply", action="store_true", help="Actually delete matched demo channels.")
    parser.add_argument("--backup", default="data/demo_cleanup_backup.json", help="Backup JSON path.")
    args = parser.parse_args()

    payload = await cleanup_demo_data(dry_run=not args.apply)
    backup_path = Path(args.backup)
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    # CRG: Keep CLI output without using production print calls.
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
