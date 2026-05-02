# -*- coding: utf-8 -*-
import urllib.request, json

print("===== Lab Recommend (correct schema) =====")
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
        print("Status:", r.status)
        print("Keys:", list(data.keys()))
        recs = data.get("recommendations") or []
        print(f"Recommendations: {len(recs)}")
        if recs:
            print(f"First: {recs[0].get('path_name')} (score: {recs[0].get('match_score')})")
except Exception as e:
    print("ERROR:", type(e).__name__, str(e)[:300])
