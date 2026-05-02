from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request


BASE_URL = os.getenv("TUBEFACTORY_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
API_PREFIX = os.getenv("TUBEFACTORY_API_PREFIX", "/api/v1").rstrip("/")


def api(path: str) -> str:
    return f"{BASE_URL}{API_PREFIX}{path}"


FEATURES = [
    (
        "Title optimization",
        api("/content-factory/title-optimization?")
        + urllib.parse.urlencode({"title": "AI tutorial", "target_audience": "tech"}),
        ["improved_title_suggestions"],
    ),
    ("Shot list", api("/content-factory/shot-list?video_duration_minutes=5&camera_count=1&has_b_roll=true"), ["shot_list"]),
    ("AI script", api("/content-factory/ai-script?niche=tech&template_id=tutorial&topic=AI"), ["segments"]),
    (
        "Thumbnail suggestions",
        api("/content-factory/thumbnail-suggestions?")
        + urllib.parse.urlencode({"title": "AI tutorial", "niche": "tech"}),
        ["concepts"],
    ),
    ("Publish time", api("/content-factory/publish-time-optimization?niche=tech"), ["time_windows"]),
    ("Human review", api("/content-factory/human-review-checklist?niche=tech&video_type=tutorial"), ["minimum_publish_gate"]),
]


def main() -> int:
    print(f"TubeFactory content-factory check: {BASE_URL}{API_PREFIX}")
    passed = 0
    failed = 0
    for name, url, expected_keys in FEATURES:
        try:
            req = urllib.request.Request(url, method="POST")
            if "human-review-checklist" in url:
                req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=15) as response:
                payload = json.dumps(json.loads(response.read().decode("utf-8")), ensure_ascii=False)
            missing = [key for key in expected_keys if key not in payload]
            if missing:
                print(f"FAIL {name}: missing {missing}")
                failed += 1
            else:
                print(f"OK   {name}")
                passed += 1
        except Exception as exc:
            print(f"FAIL {name}: {str(exc)[:120]}")
            failed += 1
    print(f"Passed: {passed}/{len(FEATURES)}, Failed: {failed}/{len(FEATURES)}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
