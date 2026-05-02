# -*- coding: utf-8 -*-
import urllib.request, urllib.error

print("===== 各分析端点详细响应 =====")
for name, path in [
    ("viral-detection", "/api/v1/analysis/viral-detection"),
    ("evergreen", "/api/v1/analysis/evergreen"),
    ("sentiment", "/api/v1/analysis/sentiment"),
    ("monetization", "/api/v1/analysis/monetization"),
]:
    try:
        req = urllib.request.Request(
            f"http://localhost:8000{path}",
            data=b'{"target_type":"video","target_id":"1","analysis_types":["viral_detection"]}',
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            print(f"  {name}: HTTP {r.status} OK")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  {name}: HTTP {e.code}")
        print(f"    Body: {body[:300]}")
    except Exception as e:
        print(f"  {name}: ERROR {type(e).__name__}: {str(e)[:100]}")
