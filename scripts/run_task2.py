import asyncio
import json
import sys
sys.path.insert(0, r"D:\Projects\YouTube\tubefactory-ocp")

from datetime import datetime, timezone
from packages.db.schema import CrawlerTask, CrawlerTaskRun, CrawlerRunStatus, get_sessionmaker
from apps.api.services.crawler_executor import execute_crawler_task

async def main():
    print("Getting session...", flush=True)
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        print("Getting task 2...", flush=True)
        task = await session.get(CrawlerTask, 2)
        print(f"Task: {task.name if task else 'NOT FOUND'}", flush=True)
        if not task:
            return

        print("Creating run...", flush=True)
        run = CrawlerTaskRun(task_id=task.id, status=CrawlerRunStatus.RUNNING)
        session.add(run)
        await session.flush()
        await session.refresh(run)
        print(f"Run id: {run.id}", flush=True)

        print("Executing...", flush=True)
        start = datetime.now(timezone.utc)
        try:
            payload = await execute_crawler_task(task, session, run_id=run.id)
            print(f"SUCCESS: {payload.get('message', '')}", flush=True)
            run.status = CrawlerRunStatus.SUCCESS
            run.items_found = payload.get("channels_passed", 0)
        except Exception as exc:
            print(f"FAILED: {exc}", flush=True)
            import traceback
            traceback.print_exc()
            run.status = CrawlerRunStatus.ERROR
            run.message = str(exc)
        finally:
            run.finished_at = datetime.now(timezone.utc)
        
        print("Committing...", flush=True)
        try:
            await session.commit()
            print("Committed", flush=True)
        except Exception as ce:
            print(f"COMMIT FAILED: {ce}", flush=True)

        elapsed = (run.finished_at - start).total_seconds()
        print(f"Elapsed: {elapsed:.1f}s, found: {run.items_found}", flush=True)

asyncio.run(main())
