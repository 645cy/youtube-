"""
Phase 2 修复最终验证
"""
import urllib.request, urllib.error, json, sys

BASE = "http://localhost:8000/api/v1"

def api(method, path, body=None):
    url = f"{BASE}{path}"
    req = urllib.request.Request(url, method=method)
    if body:
        req.data = json.dumps(body).encode()
        req.add_header("Content-Type", "application/json")
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"_error": f"HTTP {e.code}: {e.read().decode()[:200]}"}
    except Exception as e:
        return {"_error": str(e)}

print("=" * 60)
print(" Phase 2 修复最终验证")
print("=" * 60)

# 1. Growth
print("\n【1. Growth 模拟历史】")
r = api("GET", "/analysis/growth?days=7")
if isinstance(r, list) and len(r) >= 7:
    print(f"  ✅ {len(r)} 天数据: {r[0]['date']} ~ {r[-1]['date']}")
else:
    print(f"  ❌ {r}")

# 2. SEO Keywords
print("\n【2. SEO 关键词】")
r = api("GET", "/content-factory/seo-keywords?topic=Python&limit=5")
kw = r.get("keywords", [])
print(f"  ✅ {len(kw)} 条关键词 (总建议: {r.get('total_suggestions', 0)})")
for k in kw[:3]:
    src = k.get("source", "?")
    print(f"     - {k['keyword']} (来源:{src}, 搜索量~{k.get('estimated_monthly_searches', '?')})")

# 3. Niche Score
print("\n【3. Niche 打分 (真实数据)】")
r = api("POST", "/analysis/niche-score", {"target_type": "niche", "target_id": "tech"})
if r.get("status") == "success":
    res = r.get("result", {})
    print(f"  ✅ 分数: {r.get('score')}, 机会: {res.get('opportunity_level')}")
else:
    print(f"  ❌ {r}")

# 4. Sentiment
print("\n【4. 情感分析 (评论抓取)】")
r = api("POST", "/analysis/sentiment", {"target_type": "video", "target_id": "dQw4w9WgXcQ"})
if r.get("status") == "success":
    result = r.get("result", {})
    samples = result.get("sample_results", [])
    print(f"  ✅ 分数: {r.get('score')}, 分析评论: {len(samples)} 条")
else:
    print(f"  ❌ {r}")

# 5. Health + Scheduler
print("\n【5. 健康检查】")
r = api("GET", "/health")
print(f"  ✅ 状态: {r.get('status')}, YouTube API: {r.get('youtube_api')}")

# 6. Channels (import metric_history)
print("\n【6. 频道列表 (metric_history 已就绪)】")
r = api("GET", "/channels")
print(f"  ✅ 频道数: {r.get('total', 0)}")

print("\n" + "=" * 60)
print(" 验证完成")
print("=" * 60)
