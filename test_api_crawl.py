"""
通过后端 API 直接测试爬虫：
1. 创建 keyword_search 任务
2. 触发执行
3. 查看执行结果和入库数据
"""
import asyncio
import json
import sys
import urllib.request
from datetime import datetime, timezone

API_BASE = "http://localhost:8000/api/v1"


def api_call(method: str, path: str, body: dict | None = None) -> dict:
    url = f"{API_BASE}{path}"
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body else None
    req = urllib.request.Request(url, method=method, data=data, headers={
        "Content-Type": "application/json",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode("utf-8"), "status": e.code}
    except Exception as e:
        return {"error": str(e)}


def db_count():
    """查询数据库中频道和视频数量."""
    import sys
    sys.path.insert(0, "D:\\Projects\\YouTube\\tubefactory-ocp")
    from sqlalchemy import func, select
    from packages.db.schema import Channel, Video, get_sessionmaker

    async def _count():
        sessionmaker = get_sessionmaker()
        async with sessionmaker() as session:
            c = await session.execute(select(func.count(Channel.id)))
            v = await session.execute(select(func.count(Video.id)))
            return c.scalar(), v.scalar()

    return asyncio.run(_count())


def main():
    print("=" * 60)
    print("🧪 API 级爬虫抓取测试")
    print("=" * 60)

    # 1. 抓取前数据量
    print("\n📊 抓取前数据库状态:")
    channels_before, videos_before = db_count()
    print(f"   频道: {channels_before}")
    print(f"   视频: {videos_before}")

    # 2. 创建任务
    print("\n📝 创建 keyword_search 任务...")
    task = api_call("POST", "/crawler/tasks", {
        "name": f"API测试-{datetime.now(timezone.utc).strftime('%H%M%S')}",
        "task_type": "keyword_search",
        "target": "AI tools",
        "frequency": "manual",
    })
    if "error" in task:
        print(f"   ❌ 创建失败: {task['error']}")
        return 1
    task_id = task["id"]
    print(f"   ✅ 任务创建成功 ID={task_id}")

    # 3. 触发执行
    print("\n🚀 触发任务执行...")
    run = api_call("POST", f"/crawler/tasks/{task_id}/trigger")
    if "error" in run:
        print(f"   ❌ 执行失败: {run['error']}")
        return 1
    print(f"   ✅ 执行完成")
    print(f"   status: {run.get('status')}")
    print(f"   source_status: {run.get('source_status')}")
    print(f"   items_found: {run.get('items_found')}")
    print(f"   message: {run.get('message')}")

    # 4. 抓取后数据量
    print("\n📊 抓取后数据库状态:")
    channels_after, videos_after = db_count()
    print(f"   频道: {channels_after} (+{channels_after - channels_before})")
    print(f"   视频: {videos_after} (+{videos_after - videos_before})")

    # 5. 结果
    print("\n" + "=" * 60)
    if run.get("items_found", 0) > 0:
        print("🎉 抓取成功！数据已入库。")
        return 0
    else:
        print("⚠️  未抓取到数据。请检查代理配置和 VPN 状态。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
