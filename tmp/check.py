# -*- coding: utf-8 -*-
import urllib.request, json

print("===== API 空数据检查 =====")
for path in ["/api/v1/channels", "/api/v1/videos", "/api/v1/channels/tags", "/api/v1/analysis/dashboard-kpi", "/api/v1/radar/monitors"]:
    try:
        req = urllib.request.Request("http://localhost:8000" + path)
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
            item_count = len(data) if isinstance(data, list) else "obj"
            print("  " + path + ": " + str(r.status) + " - items=" + str(item_count))
    except Exception as e:
        print("  " + path + ": ERROR - " + type(e).__name__ + ": " + str(e))

print()
print("===== 页面首屏检查 =====")
for path in ["/dashboard", "/lab", "/radar", "/factory"]:
    try:
        with urllib.request.urlopen("http://localhost:3000" + path, timeout=5) as r:
            html = r.read().decode("utf-8", errors="replace")
            title = ""
            if "<title>" in html:
                title = html.split("<title>")[1].split("</title>")[0]
            empty_state = "暂无" in html or "没有找到" in html or "Empty" in html or "empty" in html.lower()
            has_mock = "MOCK_" in html
            print("  " + path + ": title=" + repr(title) + " empty_state=" + str(empty_state) + " mock=" + str(has_mock))
    except Exception as e:
        print("  " + path + ": ERROR - " + str(e))
