# -*- coding: utf-8 -*-
import urllib.request, json, os
from datetime import datetime

print("=" * 60)
print("  TubeFactory 架构快速审计")
print("=" * 60)

# 1. 基础服务
print("\n【1. 基础服务层】")
fe_ok = False
be_ok = False
try:
    with urllib.request.urlopen("http://localhost:3000/dashboard", timeout=3) as r:
        fe_ok = r.status == 200
        print(f"  {'✅' if fe_ok else '❌'} 前端 (localhost:3000): HTTP {r.status}")
except Exception as e:
    print(f"  ❌ 前端 (localhost:3000): {type(e).__name__}")

try:
    with urllib.request.urlopen("http://localhost:8000/health", timeout=3) as r:
        be_ok = r.status == 200
        print(f"  {'✅' if be_ok else '❌'} 后端 (localhost:8000): HTTP {r.status}")
except Exception as e:
    print(f"  ❌ 后端 (localhost:8000): {type(e).__name__}")

# 2. 核心 API（快速检查）
print("\n【2. 核心 API（GET 端点）】")
get_apis = [
    "/api/v1/channels",
    "/api/v1/channels/tags",
    "/api/v1/videos",
    "/api/v1/analysis/dashboard",
    "/api/v1/radar/monitors",
    "/api/v1/lab/paths",
    "/api/v1/content-factory/topic-discovery?niche=tech",
    "/api/v1/content-factory/script-templates",
    "/api/v1/content-factory/seo-keywords?topic=tech&limit=5",
]
for path in get_apis:
    try:
        req = urllib.request.Request(f"http://localhost:8000{path}")
        with urllib.request.urlopen(req, timeout=5) as r:
            print(f"  ✅ GET {path.split('?')[0]}: {r.status}")
    except Exception as e:
        print(f"  ❌ GET {path.split('?')[0]}: {type(e).__name__}")

# 3. POST API（快速检查）
print("\n【3. POST API 端点】")
post_tests = [
    ("/api/v1/content-factory/shot-list", b'{"topic":"test","duration":10}'),
    ("/api/v1/lab/recommend", json.dumps({
        "skills": [{"name": "视频剪辑", "level": 5}],
        "has_camera": False, "has_mic": False, "editing_experience": 2,
        "weekly_hours": 10, "preferred_video_length": "medium", "can_show_face": True,
        "monthly_budget_usd": 0, "willing_to_invest": False, "interests": ["科技数码"],
        "native_language": "zh", "target_audience": "global",
        "has_computer": True, "computer_os": "windows", "has_smartphone": True,
    }).encode()),
]
for path, body in post_tests:
    try:
        headers = {"Content-Type": "application/json"}
        req = urllib.request.Request(f"http://localhost:8000{path}", data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=5) as r:
            print(f"  ✅ POST {path}: {r.status}")
    except Exception as e:
        print(f"  ❌ POST {path}: {type(e).__name__} {str(e)[:60]}")

# 4. 前端构建
print("\n【4. 前端构建状态】")
standalone = r"D:\Projects\YouTube\tubefactory-ocp\apps\web\.next\standalone\server.js"
if os.path.exists(standalone):
    mtime = datetime.fromtimestamp(os.path.getmtime(standalone))
    print(f"  ✅ Standalone 构建: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
else:
    print(f"  ❌ Standalone 构建不存在")

# 5. MOCK 检查
print("\n【5. MOCK 数据检查】")
try:
    with urllib.request.urlopen("http://localhost:3000/dashboard", timeout=3) as r:
        html = r.read().decode("utf-8", errors="replace")
        has_mock = "MOCK_" in html
        print(f"  {'❌' if has_mock else '✅'} Dashboard 页面: {'含 MOCK' if has_mock else '无 MOCK'}")
except:
    print(f"  ⚠️ 无法检查")

# 6. 数据库
print("\n【6. 数据库状态】")
try:
    req = urllib.request.Request("http://localhost:8000/api/v1/channels")
    with urllib.request.urlopen(req, timeout=3) as r:
        data = json.loads(r.read().decode())
        print(f"  ✅ 数据库可访问")
        print(f"     频道数: {data.get('total', 0)} | 视频数: 待查")
except Exception as e:
    print(f"  ❌ 数据库访问失败: {e}")

# 7. 架构拓扑
print("\n【7. 架构拓扑】")
print("  浏览器 → Next.js (localhost:3000)")
print("           ↓ fetch /api/v1/*")
print("         FastAPI (localhost:8000)")
print("           ↓ SQLAlchemy + aiosqlite")
print("         SQLite (./data/tubefactory.db)")
print("           ↓ (可选) YouTube Data API")
print("         googleapis.com")

print("\n" + "=" * 60)
print("  审计完成")
print("=" * 60)
