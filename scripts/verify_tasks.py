import asyncio
import json
import sys
sys.path.insert(0, r"D:\Projects\YouTube\tubefactory-ocp")
from packages.db.schema import get_sessionmaker, CrawlerTask
from sqlalchemy import select

async def main():
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        result = await session.execute(select(CrawlerTask).order_by(CrawlerTask.id))
        tasks = result.scalars().all()
        print(f"总任务数: {len(tasks)}")
        for t in tasks:
            cfg = json.loads(t.config_json or "{}")
            kw_count = len(cfg.get("keywords", []))
            print(f"  [{t.id}] {t.name} | type={t.task_type} | freq={t.frequency} | keywords={kw_count}")

asyncio.run(main())
