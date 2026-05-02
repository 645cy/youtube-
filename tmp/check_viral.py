# -*- coding: utf-8 -*-
import urllib.request

print("===== viral-detection 详细错误 =====")
try:
    req = urllib.request.Request(
        "http://localhost:8000/api/v1/analysis/viral-detection",
        data=b'{"target_type":"video","target_id":"1","analysis_types":["viral_detection"]}',
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        print("Status:", r.status)
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print("Status:", e.code)
    print("Body:", body[:300])
