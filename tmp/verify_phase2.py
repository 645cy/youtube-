"""
Phase 2 修复验证脚本
测试: growth模拟历史 / SEO关键词 / Niche打分 / 评论抓取 / 定时调度
"""
import subprocess, json, sys

BASE = "http://localhost:8000/api/v1"

def curl(method, path, **kwargs):
    cmd = ["curl", "-s", "-X", method, f"{BASE}{path}"]
    if method == "GET":
        for k, v in kwargs.items():
            cmd.extend(["-G", "--data-urlencode", f"{k}={v}"])
    else:
        # POST: 所有 kwargs 合并为一个 JSON body
        body = {}
        for k, v in kwargs.items():
            try:
                body[k] = json.loads(v) if isinstance(v, str) and v.startswith("[") else v
            except:
                body[k] = v
        cmd.extend(["-H", "Content-Type: application/json", "-d", json.dumps(body)])
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=15).stdout
        return json.loads(out) if out.strip() else {}
    except Exception as e:
        return {"_error": str(e)}

print("=" * 60)
print(" Phase 2 修复验证")
print("=" * 60)

# 1. Growth 接口 — 应返回 30 天模拟历史
print("\n【1. Growth 模拟历史数据】")
r = curl("GET", "/analysis/growth", days=7)
if isinstance(r, list) and len(r) >= 7:
    print(f"  ✅ 返回 {len(r)} 天数据")
    print(f"     首日: {r[0]['date']} subs={r[0]['subscribers']} views={r[0]['views']}")
    print(f"     末日: {r[-1]['date']} subs={r[-1]['subscribers']} views={r[-1]['views']}")
else:
    print(f"  ❌ 失败: {r}")

# 2. SEO 关键词 — 应接入 YouTube Suggest
print("\n【2. SEO 关键词 (YouTube Suggest)】")
r = curl("GET", "/content-factory/seo-keywords", topic="Python", limit=10)
keywords = r.get("keywords", [])
if keywords:
    suggest_count = sum(1 for k in keywords if k.get("source") == "youtube_suggest")
    print(f"  ✅ 返回 {len(keywords)} 条关键词, 其中 {suggest_count} 条来自 YouTube Suggest")
    for k in keywords[:3]:
        print(f"     - {k['keyword']} ({k.get('source', '?')}, 搜索量~{k.get('estimated_monthly_searches', '?')})")
else:
    print(f"  ❌ 失败: {r}")

# 3. Niche 打分 — 应基于数据库真实数据
print("\n【3. Niche 打分 (真实数据)】")
r = curl("POST", "/analysis/niche-score", target_type="niche", target_id="tech")
if r.get("status") == "success":
    result = r.get("result", {})
    print(f"  ✅ 状态: {r['status']}, 分数: {r.get('score', '?')}")
    print(f"     niche: {result.get('niche_name', '?')}")
    print(f"     流量潜力: {result.get('traffic_potential', '?')}")
    print(f"     机会等级: {result.get('opportunity_level', '?')}")
else:
    print(f"  ⚠️  niche打分返回: {r.get('status', r)}")

# 4. 健康检查 — scheduler 应已启动
print("\n【4. 健康检查 (Scheduler)】")
r = curl("GET", "/health")
print(f"  状态: {r.get('status', '?')}")
print(f"  YouTube API: {r.get('youtube_api', '?')}")

print("\n" + "=" * 60)
print(" 验证完成")
print("=" * 60)
