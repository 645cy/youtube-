# -*- coding: utf-8 -*-
import urllib.request, json

print("===== 1. 页面 HTML 验证 =====")
for path in ["/dashboard", "/lab", "/radar", "/factory"]:
    try:
        with urllib.request.urlopen("http://localhost:3000" + path, timeout=5) as r:
            html = r.read().decode("utf-8", errors="replace")
            has_mock = "MOCK_" in html
            empty_state = "暂无" in html or "没有找到" in html or "empty" in html.lower()
            print(f"  {path}: mock={has_mock} empty_state={empty_state}")
    except Exception as e:
        print(f"  {path}: ERROR {e}")

print()
print("===== 2. API 端点验证 =====")
for path in ["/api/v1/channels", "/api/v1/analysis/dashboard", "/api/v1/radar/monitors", "/api/v1/channels/tags"]:
    try:
        req = urllib.request.Request("http://localhost:8000" + path)
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
            item_count = len(data) if isinstance(data, list) else "obj"
            print(f"  {path}: {r.status} items={item_count}")
    except Exception as e:
        print(f"  {path}: ERROR {type(e).__name__}: {str(e)[:100]}")

print()
print("===== 3. Content Factory API 验证 =====")
# topic-discovery
print("  topic-discovery:")
try:
    req = urllib.request.Request("http://localhost:8000/api/v1/content-factory/topic-discovery?niche=tech")
    with urllib.request.urlopen(req, timeout=5) as r:
        data = json.loads(r.read().decode())
        suggestions = (data.get("topic_suggestions") or []) if isinstance(data, dict) else []
        print(f"    Status: {r.status}, suggestions: {len(suggestions)}")
except Exception as e:
    print(f"    ERROR {type(e).__name__}: {str(e)[:100]}")

# shot-list
print("  shot-list:")
try:
    req = urllib.request.Request(
        "http://localhost:8000/api/v1/content-factory/shot-list",
        data=b'{"topic": "test", "duration": 10}',
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        data = json.loads(r.read().decode())
        shots = (data.get("shot_list") or []) if isinstance(data, dict) else []
        print(f"    Status: {r.status}, shots: {len(shots)}")
except Exception as e:
    print(f"    ERROR {type(e).__name__}: {str(e)[:100]}")

# title-optimization
print("  title-optimization:")
try:
    req = urllib.request.Request(
        "http://localhost:8000/api/v1/content-factory/title-optimization?title=test+video&target_audience=general&has_face_in_thumbnail=true&has_text_overlay=true",
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        data = json.loads(r.read().decode())
        print(f"    Status: {r.status}, keys: {list(data.keys())}")
except Exception as e:
    print(f"    ERROR {type(e).__name__}: {str(e)[:100]}")

# seo-keywords
print("  seo-keywords:")
try:
    req = urllib.request.Request("http://localhost:8000/api/v1/content-factory/seo-keywords?topic=tech&limit=10")
    with urllib.request.urlopen(req, timeout=5) as r:
        data = json.loads(r.read().decode())
        keywords = (data.get("keywords") or []) if isinstance(data, dict) else []
        print(f"    Status: {r.status}, keywords: {len(keywords)}")
except Exception as e:
    print(f"    ERROR {type(e).__name__}: {str(e)[:100]}")

print()
print("===== 4. Lab API 验证 =====")
print("  lab/recommend:")
try:
    req = urllib.request.Request(
        "http://localhost:8000/api/v1/lab/recommend",
        data=b'{"skills": ["video"], "available_time": 10, "budget": 0, "interests": ["tech"], "equipment": ["phone"], "experience": "beginner", "target_platforms": ["youtube"]}',
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        data = json.loads(r.read().decode())
        recs = (data.get("recommendations") or []) if isinstance(data, dict) else []
        print(f"    Status: {r.status}, recommendations: {len(recs)}")
except Exception as e:
    print(f"    ERROR {type(e).__name__}: {str(e)[:100]}")
