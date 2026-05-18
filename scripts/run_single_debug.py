import asyncio
import json
import sys
sys.path.insert(0, r"D:\Projects\YouTube\tubefactory-ocp")

from datetime import datetime, timezone
from packages.db.schema import CrawlerTask, CrawlerTaskRun, CrawlerRunStatus, get_sessionmaker
from apps.api.services.crawler_executor import execute_crawler_task
from apps.api.services.youtube_api import DualTrackExtractor
from apps.api.config import settings


async def main():
    # 先直接测试 API 搜索
    print("=== 直接测试 API 搜索 ===")
    extractor = DualTrackExtractor(api_key=settings.YOUTUBE_API_KEY)
    for kw in ['Pika Labs', 'Runway tutorial']:
        try:
            result = await extractor._api.search_list(kw, max_results=3, search_type='channel')
            print(f"  {kw}: ok, {len(result.get('items', []))} items")
        except Exception as e:
            print(f"  {kw}: FAILED {type(e).__name__}: {e}")

    print("\n=== 开始执行 CrawlerTask ===")
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        task = await session.get(CrawlerTask, 1)
        print(f"任务: [{task.id}] {task.name}")

        run = CrawlerTaskRun(task_id=task.id, status=CrawlerRunStatus.RUNNING)
        session.add(run)
        await session.flush()
        await session.refresh(run)

        start = datetime.now(timezone.utc)
        try:
            payload = await execute_crawler_task(task, session, run_id=run.id)
            run.status = CrawlerRunStatus.SUCCESS
            run.items_found = payload.get("channels_passed", 0)
            print(f"成功！发现 {payload.get('channels_found', 0)} 个频道，入库 {payload.get('channels_passed', 0)} 个")
        except Exception as exc:
            print(f"失败: {exc}")
            import traceback
            traceback.print_exc()
            run.status = CrawlerRunStatus.ERROR
        finally:
            run.finished_at = datetime.now(timezone.utc)
        await session.commit()

        elapsed = (run.finished_at - start).total_seconds()
        print(f"耗时: {elapsed:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
