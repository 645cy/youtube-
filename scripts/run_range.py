"""运行指定范围的 channel_discovery 任务."""
import asyncio
import json
import sys
sys.path.insert(0, r"D:\Projects\YouTube\tubefactory-ocp")

from datetime import datetime, timezone
from packages.db.schema import CrawlerTask, CrawlerTaskRun, CrawlerRunStatus, get_sessionmaker
from apps.api.services.crawler_executor import execute_crawler_task


async def run_task(task_id: int) -> dict:
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        task = await session.get(CrawlerTask, task_id)
        if not task:
            return {"task_id": task_id, "status": "missing", "found": 0}

        print(f"  Running [{task.id}] {task.name} ...", flush=True)
        run = CrawlerTaskRun(task_id=task.id, status=CrawlerRunStatus.RUNNING)
        session.add(run)
        await session.flush()
        await session.refresh(run)

        start = datetime.now(timezone.utc)
        try:
            payload = await execute_crawler_task(task, session, run_id=run.id)
            run.status = CrawlerRunStatus.SUCCESS
            run.items_found = payload.get("channels_passed", 0)
            run.result_json = json.dumps(payload, ensure_ascii=False)
        except Exception as exc:
            print(f"  ERROR: {exc}")
            run.status = CrawlerRunStatus.ERROR
            run.message = str(exc)
        finally:
            run.finished_at = datetime.now(timezone.utc)
            task.last_run_at = run.finished_at
            try:
                await session.commit()
            except Exception as ce:
                print(f"  COMMIT ERROR: {ce}")

        elapsed = (run.finished_at - start).total_seconds()
        print(f"  -> {run.items_found} 频道, {elapsed:.1f}s, {run.status.value}", flush=True)
        return {"task_id": task_id, "status": run.status.value, "found": run.items_found}


async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=3)
    parser.add_argument("--end", type=int, default=15)
    args = parser.parse_args()

    print(f"Running tasks {args.start}~{args.end} ...", flush=True)
    results = []
    for task_id in range(args.start, args.end + 1):
        r = await run_task(task_id)
        results.append(r)

    total_found = sum(r.get("found", 0) for r in results)
    print(f"\nDone! Added {total_found} channels", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
