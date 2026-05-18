"""后台批量执行 channel_discovery 任务."""
import asyncio
import sys
import os

sys.path.insert(0, r"D:\Projects\YouTube\tubefactory-ocp")
sys.path.insert(0, r"D:\Projects\YouTube\tubefactory-ocp\apps\api")
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///D:/Projects/YouTube/tubefactory-ocp/data/tubefactory.db"

from datetime import datetime, timezone
from sqlalchemy import select
from packages.db.schema import get_sessionmaker, CrawlerTask, CrawlerTaskRun, CrawlerRunStatus
from services.crawler_executor import execute_crawler_task


async def run_pending_tasks():
    sessionmaker = get_sessionmaker()

    async with sessionmaker() as session:
        result = await session.execute(
            select(CrawlerTask)
            .where(CrawlerTask.task_type == "channel_discovery")
            .where(CrawlerTask.status == "active")
            .order_by(CrawlerTask.id)
        )
        tasks = result.scalars().all()

    print(f"[{datetime.now().strftime('%H:%M:%S')}] 发现 {len(tasks)} 个待执行 channel_discovery 任务")

    for i, task in enumerate(tasks, 1):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始任务 {i}/{len(tasks)}: {task.name}")
        async with sessionmaker() as session:
            run = CrawlerTaskRun(
                task_id=task.id,
                status=CrawlerRunStatus.RUNNING,
                started_at=datetime.now(timezone.utc),
            )
            session.add(run)
            await session.commit()
            run_id = run.id

        try:
            async with sessionmaker() as session:
                await execute_crawler_task(task, session, run_id=run_id)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 完成: {task.name}")
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 失败: {task.name} - {e}")
            async with sessionmaker() as session:
                run = await session.get(CrawlerTaskRun, run_id)
                if run:
                    run.status = CrawlerRunStatus.FAILED
                    run.error_message = str(e)[:500]
                    run.finished_at = datetime.now(timezone.utc)
                    await session.commit()
        await asyncio.sleep(3)

    print(f"[{datetime.now().strftime('%H:%M:%S')}] 全部完成")


if __name__ == "__main__":
    asyncio.run(run_pending_tasks())
