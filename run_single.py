import sys, os, asyncio
sys.path.insert(0, '.')
sys.path.insert(0, './apps/api')
from datetime import datetime, timezone
from sqlalchemy import select
from packages.db.schema import get_sessionmaker, CrawlerTask, CrawlerTaskRun, CrawlerRunStatus
from services.crawler_executor import execute_crawler_task

async def run_one(task_id):
    sm = get_sessionmaker()
    async with sm() as session:
        result = await session.execute(
            select(CrawlerTask).where(CrawlerTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        if not task:
            print(f'ERROR: Task {task_id} not found')
            return
    async with sm() as session:
        run = CrawlerTaskRun(task_id=task.id, status=CrawlerRunStatus.RUNNING, started_at=datetime.now(timezone.utc))
        session.add(run)
        await session.commit()
        run_id = run.id
    try:
        async with sm() as session:
            r = await execute_crawler_task(task, session, run_id=run_id)
        found = r.get('channels_found', 0)
        passed = r.get('channels_passed', 0)
        print(f'SUCCESS: task_id={task_id} name={task.name} found={found} passed={passed}')
    except Exception as e:
        print(f'ERROR: task_id={task_id} name={task.name} error={e}')

if __name__ == '__main__':
    task_id = int(sys.argv[1])
    asyncio.run(run_one(task_id))
