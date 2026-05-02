# -*- coding: utf-8 -*-
import urllib.request, json

print("===== Title Optimization =====")
try:
    req = urllib.request.Request(
        "http://localhost:8000/api/v1/content-factory/title-optimization",
        data=b'{"title": "test video", "niche": "tech"}',
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        data = json.loads(r.read().decode())
        print("Status:", r.status)
        print("Type:", type(data).__name__)
        print("Keys:", list(data.keys()) if isinstance(data, dict) else "N/A")
        print("Response:", json.dumps(data, ensure_ascii=False, indent=2)[:500])
except Exception as e:
    print("ERROR:", type(e).__name__, str(e)[:200])

print()
print("===== SEO Keywords =====")
try:
    req = urllib.request.Request("http://localhost:8000/api/v1/content-factory/seo-keywords?niche=tech")
    with urllib.request.urlopen(req, timeout=5) as r:
        data = json.loads(r.read().decode())
        print("Status:", r.status)
        print("Type:", type(data).__name__)
        print("Keys:", list(data.keys()) if isinstance(data, dict) else "N/A")
        print("Response:", json.dumps(data, ensure_ascii=False, indent=2)[:500])
except Exception as e:
    print("ERROR:", type(e).__name__, str(e)[:200])

print()
print("===== Lab Paths =====")
try:
    req = urllib.request.Request("http://localhost:8000/api/v1/lab/paths")
    with urllib.request.urlopen(req, timeout=5) as r:
        data = json.loads(r.read().decode())
        print("Status:", r.status)
        print("Type:", type(data).__name__)
        if isinstance(data, list):
            print("Array length:", len(data))
        else:
            print("Keys:", list(data.keys()) if isinstance(data, dict) else "N/A")
except Exception as e:
    print("ERROR:", type(e).__name__, str(e)[:200])
