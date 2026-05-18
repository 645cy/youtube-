import sys, os, asyncio
sys.path.insert(0, '.')
sys.path.insert(0, './apps/api')
from datetime import datetime, timezone
from sqlalchemy import select
from packages.db.schema import get_sessionmaker, CrawlerTask, CrawlerTaskRun, CrawlerRunStatus
from services.crawler_executor import execute_crawler_task

async def run_batch(task_ids):
    sm = get_sessionmaker()
    async with sm() as session:
        result = await session.execute(
            select(CrawlerTask).where(CrawlerTask.id.in_(task_ids)).order_by(CrawlerTask.id)
        )
        tasks = result.scalars().all()
    total_found = 0
    total_passed = 0
    errors = []
    for i, task in enumerate(tasks, 1):
        t = datetime.now().strftime('%H:%M:%S')
        print(f'[{t}] [{i}/{len(tasks)}] ID={task.id} {task.name} ...')
        async with sm() as session:
            run = CrawlerTaskRun(task_id=task.id, status=CrawlerRunStatus.RUNNING, started_at=datetime.now(timezone.utc))
            session.add(run)
            await session.commit()
            run_id = run.id
        try:
            async with sm() as session:
                r = await asyncio.wait_for(execute_crawler_task(task, session, run_id=run_id), timeout=240)
            found = r.get('channels_found', 0)
            passed = r.get('channels_passed', 0)
            total_found += found
            total_passed += passed
            t = datetime.now().strftime('%H:%M:%S')
            print(f'[{t}] [{i}/{len(tasks)}] {task.name} -> found={found} passed={passed}')
        except asyncio.TimeoutError:
            errors.append(f'{task.name}: 超时(>240s)')
            t = datetime.now().strftime('%H:%M:%S')
            print(f'[{t}] [{i}/{len(tasks)}] {task.name} -> ERROR: 超时(>240s)')
        except Exception as e:
            errors.append(f'{task.name}: {e}')
            t = datetime.now().strftime('%H:%M:%S')
            print(f'[{t}] [{i}/{len(tasks)}] {task.name} -> ERROR: {e}')
        await asyncio.sleep(3)
    print(f'BATCH_SUMMARY: tasks={len(tasks)} found={total_found} passed={total_passed} errors={len(errors)}')
    for e in errors:
        print(f'ERROR_DETAIL: {e}')
    return total_found, total_passed, errors

if __name__ == '__main__':
    task_ids = [int(x) for x in sys.argv[1:]]
    asyncio.run(run_batch(task_ids))
