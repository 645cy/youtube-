# -*- coding: utf-8 -*-
import urllib.request, json

print("===== Title Optimization (query params) =====")
try:
    req = urllib.request.Request(
        "http://localhost:8000/api/v1/content-factory/title-optimization?title=test+video&target_audience=general&has_face_in_thumbnail=true&has_text_overlay=true",
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        data = json.loads(r.read().decode())
        print("Status:", r.status)
        print("Keys:", list(data.keys()))
        print("Response:", json.dumps(data, ensure_ascii=False, indent=2)[:500])
except Exception as e:
    print("ERROR:", type(e).__name__, str(e)[:200])

print()
print("===== SEO Keywords (correct params) =====")
try:
    req = urllib.request.Request("http://localhost:8000/api/v1/content-factory/seo-keywords?topic=tech&limit=10")
    with urllib.request.urlopen(req, timeout=5) as r:
        data = json.loads(r.read().decode())
        print("Status:", r.status)
        print("Keys:", list(data.keys()) if isinstance(data, dict) else "N/A")
        print("Response:", json.dumps(data, ensure_ascii=False, indent=2)[:500])
except Exception as e:
    print("ERROR:", type(e).__name__, str(e)[:200])
