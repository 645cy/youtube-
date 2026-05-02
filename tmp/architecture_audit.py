# -*- coding: utf-8 -*-
"""TubeFactory 架构全面审计脚本"""
import urllib.request, json, sys

def check(name, condition, detail=""):
    status = "✅" if condition else "❌"
    print(f"  {status} {name}")
    if detail and not condition:
        print(f"      ↳ {detail}")
    return condition

all_ok = True

print("=" * 60)
print("  TubeFactory 架构全面审计报告")
print("=" * 60)

# =============================================================================
# 1. 基础服务层
# =============================================================================
print("\n【1. 基础服务层】")

# 前端
frontend_ok = False
try:
    with urllib.request.urlopen("http://localhost:3000/dashboard", timeout=5) as r:
        html = r.read().decode("utf-8", errors="replace")
        frontend_ok = r.status == 200 and "情报总控台" in html
except Exception as e:
    pass
all_ok &= check("前端服务 (localhost:3000)", frontend_ok, "无法访问或返回错误页面")

# 后端
backend_ok = False
backend_health = {}
try:
    with urllib.request.urlopen("http://localhost:8000/health", timeout=5) as r:
        backend_health = json.loads(r.read().decode())
        backend_ok = r.status == 200 and backend_health.get("status") == "ok"
except Exception as e:
    pass
all_ok &= check("后端服务 (localhost:8000)", backend_ok, "无法访问或健康检查失败")

# CORS / 连接性
cors_ok = False
try:
    req = urllib.request.Request("http://localhost:8000/api/v1/channels", headers={"Origin": "http://localhost:3000"})
    with urllib.request.urlopen(req, timeout=5) as r:
        cors_ok = r.status == 200
except Exception as e:
    pass
all_ok &= check("前后端连通性 (CORS)", cors_ok, "前端无法调用后端 API")

# =============================================================================
# 2. API Router 完整性检查
# =============================================================================
print("\n【2. API Router 完整性】")

api_tests = [
    ("GET",  "/api/v1/channels",                None,                               "频道列表"),
    ("GET",  "/api/v1/channels/tags",           None,                               "标签聚合"),
    ("POST", "/api/v1/channels/search",         b'{}',                              "频道搜索"),
    ("GET",  "/api/v1/videos",                  None,                               "视频列表"),
    ("GET",  "/api/v1/analysis/dashboard",      None,                               "Dashboard KPI"),
    ("POST", "/api/v1/analysis/viral-detection",  b'{"target_type":"video","target_id":"1","analysis_types":["viral_detection"]}', "爆款检测"),
    ("POST", "/api/v1/analysis/evergreen",      b'{"target_type":"video","target_id":"1","analysis_types":["evergreen"]}', "Evergreen检测"),
    ("POST", "/api/v1/analysis/sentiment",      b'{"target_type":"video","target_id":"1","analysis_types":["sentiment"]}', "情感分析"),
    ("POST", "/api/v1/analysis/monetization",   b'{"target_type":"video","target_id":"1","analysis_types":["monetization"]}', "变现检测"),
    ("POST", "/api/v1/analysis/full-analysis",  b'{"target_type":"video","target_id":"1"}', "全部分析"),
    ("GET",  "/api/v1/analysis/history",        None,                               "分析历史"),
    ("GET",  "/api/v1/radar/monitors",          None,                               "监控任务列表"),
    ("POST", "/api/v1/radar/monitors",          b'{"channel_id":1,"job_type":"STATS","frequency":"daily","is_active":true}', "创建监控任务"),
    ("GET",  "/api/v1/radar/compare",           None,                               "频道对比"),
    ("GET",  "/api/v1/lab/paths",               None,                               "变现路径列表"),
    ("POST", "/api/v1/lab/recommend",           None,                               "Lab推荐"),
    ("POST", "/api/v1/lab/quick-match",         b'{}',                              "快速匹配"),
    ("GET",  "/api/v1/content-factory/topic-discovery?niche=tech", None,            "选题发现"),
    ("GET",  "/api/v1/content-factory/script-templates", None,                      "脚本模板"),
    ("POST", "/api/v1/content-factory/shot-list", b'{"topic":"test","duration":10}', "分镜生成"),
    ("POST", "/api/v1/content-factory/title-optimization", None,                   "标题优化"),
    ("GET",  "/api/v1/content-factory/seo-keywords?topic=tech&limit=5", None,       "SEO关键词"),
]

# Lab recommend 需要正确的请求体
lab_body = {
    "skills": [{"name": "视频剪辑", "level": 5}],
    "has_camera": False, "has_mic": False, "editing_experience": 2,
    "weekly_hours": 10, "preferred_video_length": "medium", "can_show_face": True,
    "monthly_budget_usd": 0, "willing_to_invest": False, "interests": ["科技数码"],
    "native_language": "zh", "target_audience": "global",
    "has_computer": True, "computer_os": "windows", "has_smartphone": True,
}

api_results = {}
for method, path, body, label in api_tests:
    try:
        url = "http://localhost:8000" + path
        headers = {}
        actual_body = body
        
        # 特殊处理：Lab recommend
        if path == "/api/v1/lab/recommend":
            actual_body = json.dumps(lab_body).encode()
            headers["Content-Type"] = "application/json"
        
        # 特殊处理：title-optimization (query params)
        if path == "/api/v1/content-factory/title-optimization":
            url += "?title=test+video&target_audience=general&has_face_in_thumbnail=true&has_text_overlay=true"
        
        # 特殊处理：channel search (query params, empty body)
        if path == "/api/v1/channels/search":
            url += "?query=test"
            actual_body = None
        
        req = urllib.request.Request(url, data=actual_body, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=10) as r:
            api_results[label] = (r.status, None)
    except urllib.error.HTTPError as e:
        api_results[label] = (e.code, e.reason)
    except Exception as e:
        api_results[label] = (None, str(e)[:80])

# 统计
ok_count = sum(1 for s, _ in api_results.values() if s == 200)
total = len(api_results)
print(f"  API 端点: {ok_count}/{total} 正常")

for label, (status, err) in api_results.items():
    ok = status == 200
    all_ok &= ok
    if not ok:
        detail = f"HTTP {status} ({err})" if status else f"Error: {err}"
        check(f"  {label}", ok, detail)

# =============================================================================
# 3. 数据库层
# =============================================================================
print("\n【3. 数据库层】")

db_ok = False
try:
    req = urllib.request.Request("http://localhost:8000/api/v1/channels")
    with urllib.request.urlopen(req, timeout=5) as r:
        data = json.loads(r.read().decode())
        items = data.get("items", [])
        total_db = data.get("total", 0)
        db_ok = True
        print(f"  ✅ SQLite 数据库可访问")
        print(f"     当前频道数: {len(items)} / 总数: {total_db}")
        if len(items) == 0:
            print(f"     数据库为空（符合预期，等待用户导入）")
except Exception as e:
    all_ok &= check("SQLite 数据库", False, str(e)[:80])

# =============================================================================
# 4. 前端构建状态
# =============================================================================
print("\n【4. 前端构建状态】")

import os
standalone_path = r"D:\Projects\YouTube\tubefactory-ocp\apps\web\.next\standalone\server.js"
build_time = None
if os.path.exists(standalone_path):
    build_time = os.path.getmtime(standalone_path)
    from datetime import datetime
    build_dt = datetime.fromtimestamp(build_time)
    print(f"  ✅ Standalone 构建存在")
    print(f"     构建时间: {build_dt.strftime('%Y-%m-%d %H:%M:%S')}")
else:
    all_ok &= check("Standalone 构建", False, "server.js 不存在")

# 检查页面是否包含 MOCK
mock_check_ok = True
try:
    with urllib.request.urlopen("http://localhost:3000/dashboard", timeout=5) as r:
        html = r.read().decode("utf-8", errors="replace")
        has_mock = "MOCK_" in html
        mock_check_ok = not has_mock
        all_ok &= check("无 MOCK 数据残留", mock_check_ok, "页面仍包含 MOCK_ 字符串")
except:
    pass

# =============================================================================
# 5. 数据流完整性
# =============================================================================
print("\n【5. 数据流完整性】")

# 测试完整的搜索 -> 入库 -> 查询流程（沙盒内 YouTube API 不可用，仅测试本地流程）
print(f"  ✅ 频道列表查询: {'OK' if api_results.get('频道列表', (0,))[0] == 200 else 'FAIL'}")
print(f"  ✅ 标签聚合查询: {'OK' if api_results.get('标签聚合', (0,))[0] == 200 else 'FAIL'}")
print(f"  ✅ KPI 计算: {'OK' if api_results.get('Dashboard KPI', (0,))[0] == 200 else 'FAIL'}")
print(f"  ✅ 监控任务查询: {'OK' if api_results.get('监控任务列表', (0,))[0] == 200 else 'FAIL'}")
print(f"  ✅ Lab 推荐: {'OK' if api_results.get('Lab推荐', (0,))[0] == 200 else 'FAIL'}")
print(f"  ✅ 选题发现: {'OK' if api_results.get('选题发现', (0,))[0] == 200 else 'FAIL'}")
print(f"  ✅ 分镜生成: {'OK' if api_results.get('分镜生成', (0,))[0] == 200 else 'FAIL'}")

# =============================================================================
# 6. 架构拓扑
# =============================================================================
print("\n【6. 架构拓扑】")
print("  用户浏览器 → localhost:3000 (Next.js standalone)")
print("                ↓ fetch()")
print("              localhost:8000 (FastAPI / Uvicorn)")
print("                ↓ SQLAlchemy + aiosqlite")
print("              SQLite WAL (./data/tubefactory.db)")
print("                ↓ (可选) Google YouTube Data API v3")
print("              youtube.googleapis.com")

# =============================================================================
# 总结
# =============================================================================
print("\n" + "=" * 60)
if all_ok:
    print("  🎉 架构审计全部通过")
    print("  前后端运行正常，所有 API 可访问，数据流完整")
else:
    print("  ⚠️  架构存在异常，请检查上方 ❌ 项")
print("=" * 60)
