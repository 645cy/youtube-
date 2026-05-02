# -*- coding: utf-8 -*-
import urllib.request, json

print("=" * 60)
print(" TubeFactory 真实用户体验筛查 - 最终验证")
print("=" * 60)

# 1. 页面 HTML 验证
print("\n【1. 页面首屏验证】")
all_ok = True
for path in ["/dashboard", "/lab", "/radar", "/factory"]:
    try:
        with urllib.request.urlopen("http://localhost:3000" + path, timeout=5) as r:
            html = r.read().decode("utf-8", errors="replace")
            has_mock = "MOCK_" in html
            if has_mock:
                print(f"  ❌ {path}: 仍包含 MOCK 数据")
                all_ok = False
            else:
                print(f"  ✅ {path}: 无 MOCK 数据")
    except Exception as e:
        print(f"  ❌ {path}: 无法访问 ({e})")
        all_ok = False

# 2. API 验证
print("\n【2. 核心 API 验证】")
api_tests = [
    ("GET", "/api/v1/channels", None),
    ("GET", "/api/v1/analysis/dashboard", None),
    ("GET", "/api/v1/radar/monitors", None),
    ("GET", "/api/v1/channels/tags", None),
    ("GET", "/api/v1/content-factory/topic-discovery?niche=tech", None),
    ("POST", "/api/v1/content-factory/shot-list", b'{"topic": "test", "duration": 10}'),
    ("POST", "/api/v1/content-factory/title-optimization", None),  # query params
    ("GET", "/api/v1/content-factory/seo-keywords?topic=tech&limit=10", None),
]
for method, path, body in api_tests:
    try:
        url = "http://localhost:8000" + path
        if path == "/api/v1/content-factory/title-optimization":
            url += "?title=test+video&target_audience=general&has_face_in_thumbnail=true&has_text_overlay=true"
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"} if body else {}, method=method)
        with urllib.request.urlopen(req, timeout=5) as r:
            print(f"  ✅ {method} {path.split('?')[0]}: {r.status}")
    except Exception as e:
        print(f"  ❌ {method} {path.split('?')[0]}: {type(e).__name__}")
        all_ok = False

# 3. Lab recommend 验证
print("\n【3. Lab Recommend API 验证】")
try:
    body = {
        "skills": [{"name": "视频剪辑", "level": 5}],
        "has_camera": False,
        "has_mic": False,
        "editing_experience": 2,
        "weekly_hours": 10,
        "preferred_video_length": "medium",
        "can_show_face": True,
        "monthly_budget_usd": 0,
        "willing_to_invest": False,
        "interests": ["科技数码"],
        "native_language": "zh",
        "target_audience": "global",
        "has_computer": True,
        "computer_os": "windows",
        "has_smartphone": True,
    }
    req = urllib.request.Request(
        "http://localhost:8000/api/v1/lab/recommend",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read().decode())
        recs = data.get("recommendations") or []
        print(f"  ✅ POST /api/v1/lab/recommend: {r.status}, {len(recs)} 条推荐")
except Exception as e:
    print(f"  ❌ POST /api/v1/lab/recommend: {type(e).__name__}: {str(e)[:100]}")
    all_ok = False

# 4. 数据源验证
print("\n【4. 数据源验证】")
try:
    req = urllib.request.Request("http://localhost:8000/api/v1/channels")
    with urllib.request.urlopen(req, timeout=5) as r:
        data = json.loads(r.read().decode())
        items = data.get("items") or []
        print(f"  数据库频道数: {len(items)} (应为 0，空状态)")
        if len(items) == 0:
            print("  ✅ 数据库为空，依赖用户搜索导入")
        else:
            print("  ⚠️ 数据库有预置数据")
except Exception as e:
    print(f"  ❌ 无法获取频道列表: {e}")

print("\n" + "=" * 60)
if all_ok:
    print("  🎉 所有验证通过！")
else:
    print("  ⚠️ 存在验证失败项，请检查上方日志")
print("=" * 60)
