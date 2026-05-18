"""测试运行单个任务，验证修复后的 API 搜索是否正常."""
import asyncio
import json
import sys
sys.path.insert(0, r"D:\Projects\YouTube\tubefactory-ocp")

from datetime import datetime, timezone
from packages.db.schema import CrawlerTask, CrawlerTaskRun, CrawlerRunStatus, get_sessionmaker
from apps.api.services.crawler_executor import execute_crawler_task


async def main():
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        task = await session.get(CrawlerTask, 1)
        if not task:
            print("任务 1 不存在")
            return

        print(f"运行: [{task.id}] {task.name}")
        cfg = json.loads(task.config_json or "{}")
        print(f"关键词: {len(cfg.get('keywords', []))}")

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
            print(f"成功！发现 {payload.get('channels_found', 0)} 个频道，入库 {payload.get('channels_passed', 0)} 个")
            print(f"消息: {payload.get('message', '')}")
        except Exception as exc:
            print(f"失败: {exc}")
            import traceback
            traceback.print_exc()
            run.status = CrawlerRunStatus.ERROR
            run.source_status = "error"
            run.message = str(exc)
        finally:
            run.finished_at = datetime.now(timezone.utc)
            task.last_run_at = run.finished_at
        await session.commit()

        elapsed = (run.finished_at - start).total_seconds()
        print(f"耗时: {elapsed:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
