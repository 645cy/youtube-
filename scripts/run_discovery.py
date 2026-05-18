"""直接运行频道发现任务，无需启动后端 HTTP 服务."""
from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone

sys.path.insert(0, r"D:\Projects\YouTube\tubefactory-ocp")

from sqlalchemy import select
from packages.db.schema import CrawlerTask, CrawlerTaskRun, CrawlerRunStatus, get_sessionmaker
from apps.api.services.crawler_executor import execute_crawler_task


async def run_task(task_id: int) -> dict:
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        task = await session.get(CrawlerTask, task_id)
        if not task:
            print(f"任务 {task_id} 不存在")
            return {}

        print(f"\n{'='*60}")
        print(f"开始运行: [{task.id}] {task.name}")
        print(f"关键词数: {len(json.loads(task.config_json or '{}').get('keywords', []))}")
        print(f"{'='*60}")

        run = CrawlerTaskRun(task_id=task.id, status=CrawlerRunStatus.RUNNING)
        session.add(run)
        await session.flush()
        await session.refresh(run)

        start = datetime.now(timezone.utc)
        try:
            payload = await execute_crawler_task(task, session, run_id=run.id)
            run.status = CrawlerRunStatus.SUCCESS
            run.source_status = payload["source_status"]
            run.message = payload["message"]
            run.items_found = payload.get("channels_passed", 0)
            run.result_json = json.dumps(payload, ensure_ascii=False)
        except Exception as exc:
            print(f"  ERROR: {exc}")
            import traceback
            traceback.print_exc()
            run.status = CrawlerRunStatus.ERROR
            run.source_status = "error"
            run.message = str(exc)
            run.items_found = 0
            run.result_json = json.dumps({"error": str(exc)}, ensure_ascii=False)
        finally:
            run.finished_at = datetime.now(timezone.utc)
            task.last_run_at = run.finished_at

        await session.commit()

        elapsed = (run.finished_at - start).total_seconds()
        print(f"  状态: {run.status.value}")
        print(f"  发现频道: {run.items_found}")
        print(f"  耗时: {elapsed:.1f}s")
        if run.message:
            print(f"  消息: {run.message[:120]}")

        return {"task_id": task_id, "status": run.status.value, "found": run.items_found}


async def main():
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        result = await session.execute(
            select(CrawlerTask).where(CrawlerTask.task_type == "channel_discovery").order_by(CrawlerTask.id)
        )
        tasks = result.scalars().all()
        print(f"发现 {len(tasks)} 个 channel_discovery 任务")
        for t in tasks:
            cfg = json.loads(t.config_json or "{}")
            print(f"  [{t.id}] {t.name} ({len(cfg.get('keywords', []))} 关键词)")

    # 串行执行，避免 API 配额瞬间打满
    print(f"\n开始串行执行 {len(tasks)} 个任务...")
    results = []
    for task in tasks:
        r = await run_task(task.id)
        results.append(r)
        # 任务间短暂停顿，避免被限流
        await asyncio.sleep(2)

    total_found = sum(r.get("found", 0) for r in results)
    print(f"\n{'='*60}")
    print(f"全部完成！共发现 {total_found} 个频道")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
