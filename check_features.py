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
    ("Channels", "GET", api("/channels"), ["items"]),
    ("Channel tags", "GET", api("/channels/tags"), []),
    ("Dashboard KPI", "GET", api("/analysis/dashboard"), ["total_channels", "total_videos"]),
    ("Lab paths", "GET", api("/lab/paths"), ["path_id"]),
    ("Radar monitors", "GET", api("/radar/monitors"), []),
    ("Topic discovery", "GET", api("/content-factory/topic-discovery?niche=tech"), ["topic_suggestions"]),
    (
        "Title optimization",
        "POST",
        api("/content-factory/title-optimization?")
        + urllib.parse.urlencode({"title": "AI tutorial", "target_audience": "tech"}),
        ["improved_title_suggestions"],
    ),
    ("Shot list", "POST", api("/content-factory/shot-list?video_duration_minutes=5&camera_count=1&has_b_roll=true"), ["shot_list"]),
    ("AI script", "POST", api("/content-factory/ai-script?niche=tech&template_id=tutorial&topic=AI"), ["segments"]),
    (
        "Thumbnail suggestions",
        "POST",
        api("/content-factory/thumbnail-suggestions?")
        + urllib.parse.urlencode({"title": "AI tutorial", "niche": "tech"}),
        ["concepts"],
    ),
    ("Publish time", "POST", api("/content-factory/publish-time-optimization?niche=tech"), ["time_windows"]),
    ("Crawler tasks", "GET", api("/crawler/tasks"), []),
]


def request_json(method: str, url: str) -> object:
    req = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    print("=" * 80)
    print(f"TubeFactory feature check: {BASE_URL}{API_PREFIX}")
    print("=" * 80)
    passed = 0
    failed = 0

    for name, method, url, expected_keys in FEATURES:
        try:
            result = request_json(method, url)
            payload = json.dumps(result, ensure_ascii=False)
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

    print("=" * 80)
    print(f"Passed: {passed}/{len(FEATURES)}")
    print(f"Failed: {failed}/{len(FEATURES)}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
