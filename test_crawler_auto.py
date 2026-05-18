"""
爬虫自动抓取测试脚本
直接在代码层面验证 Crawler 修复：
1. 创建 keyword_search 任务（搜索 AI tools）
2. 执行爬虫任务
3. 打印抓取结果
"""
import asyncio
import sys
from datetime import datetime, timezone

sys.path.insert(0, "D:\\Projects\\YouTube\\tubefactory-ocp")

from sqlalchemy.ext.asyncio import AsyncSession
from packages.db.schema import (
    get_sessionmaker,
    CrawlerTask,
    CrawlerTaskRun,
    CrawlerRunStatus,
)
from apps.api.services.crawler_executor import execute_crawler_task
from packages.db.schema import init_db


async def test_keyword_search():
    """测试关键词搜索爬虫 — 自动导入频道+视频."""
    print("=" * 60)
    print("【测试 1】关键词搜索: AI tools")
    print("=" * 60)

    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        # 创建临时任务
        task = CrawlerTask(
            name="自动测试-关键词搜索-AI-tools",
            task_type="keyword_search",
            target="AI tools",
            frequency="manual",
            status="active",
        )
        session.add(task)
        await session.flush()

        # 创建运行记录
        run = CrawlerTaskRun(task_id=task.id, status=CrawlerRunStatus.RUNNING)
        session.add(run)
        await session.flush()

        try:
            start = datetime.now(timezone.utc)
            payload = await execute_crawler_task(task, session)
            elapsed = (datetime.now(timezone.utc) - start).total_seconds()

            run.status = CrawlerRunStatus.SUCCESS
            run.source_status = payload.get("source_status", "unknown")
            run.message = payload.get("message", "")
            run.items_found = payload.get("channels_imported", 0) + payload.get("videos_imported", 0)
            import json
            run.result_json = json.dumps(payload, ensure_ascii=False)

            print(f"\n✅ 执行成功 ({elapsed:.1f}s)")
            print(f"   source_status: {payload.get('source_status')}")
            print(f"   message: {payload.get('message')}")
            print(f"   channels_imported: {payload.get('channels_imported', 0)}")
            print(f"   videos_imported: {payload.get('videos_imported', 0)}")

        except Exception as exc:
            run.status = CrawlerRunStatus.ERROR
            run.source_status = "error"
            run.message = str(exc)
            print(f"\n❌ 执行失败: {exc}")
            import traceback
            traceback.print_exc()

        run.finished_at = datetime.now(timezone.utc)
        task.last_run_at = run.finished_at
        await session.commit()
        return run.status == CrawlerRunStatus.SUCCESS


async def test_channel_latest_auto_import():
    """测试频道最新视频 — 本地无频道时自动导入."""
    print("\n" + "=" * 60)
    print("【测试 2】频道最新视频: @mkbhd (自动导入)")
    print("=" * 60)

    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        # 创建临时任务
        task = CrawlerTask(
            name="自动测试-频道视频-mkbhd",
            task_type="channel_latest",
            target="@mkbhd",
            frequency="manual",
            status="active",
        )
        session.add(task)
        await session.flush()

        run = CrawlerTaskRun(task_id=task.id, status=CrawlerRunStatus.RUNNING)
        session.add(run)
        await session.flush()

        try:
            start = datetime.now(timezone.utc)
            payload = await execute_crawler_task(task, session)
            elapsed = (datetime.now(timezone.utc) - start).total_seconds()

            run.status = CrawlerRunStatus.SUCCESS
            run.source_status = payload.get("source_status", "unknown")
            run.message = payload.get("message", "")
            run.items_found = len(payload.get("items", []))
            import json
            run.result_json = json.dumps(payload, ensure_ascii=False)

            print(f"\n✅ 执行成功 ({elapsed:.1f}s)")
            print(f"   source_status: {payload.get('source_status')}")
            print(f"   message: {payload.get('message')}")
            print(f"   items_found: {len(payload.get('items', []))}")
            if payload.get("items"):
                print(f"   first item: {payload['items'][0].get('title', 'N/A')[:60]}...")

        except Exception as exc:
            run.status = CrawlerRunStatus.ERROR
            run.source_status = "error"
            run.message = str(exc)
            print(f"\n❌ 执行失败: {exc}")
            import traceback
            traceback.print_exc()

        run.finished_at = datetime.now(timezone.utc)
        task.last_run_at = run.finished_at
        await session.commit()
        return run.status == CrawlerRunStatus.SUCCESS


async def main():
    print("\n🔧 TubeFactory 爬虫自动抓取测试")
    print(f"   时间: {datetime.now(timezone.utc).isoformat()}")
    print()

    # 初始化数据库（创建缺失的表）
    print("📦 初始化数据库...")
    await init_db(create_missing_tables=True)
    print("   数据库就绪\n")

    ok1 = await test_keyword_search()
    ok2 = await test_channel_latest_auto_import()

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    print(f"   关键词搜索:     {'✅ 通过' if ok1 else '❌ 失败'}")
    print(f"   频道视频(自动): {'✅ 通过' if ok2 else '❌ 失败'}")
    print()

    if ok1 and ok2:
        print("🎉 全部通过！爬虫修复成功。")
        return 0
    else:
        print("⚠️  部分失败，请检查日志。")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
