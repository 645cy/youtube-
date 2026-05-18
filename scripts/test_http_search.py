import httplib2, json, re, sys
sys.path.insert(0, r"D:\Projects\YouTube\tubefactory-ocp")
from apps.api.config import settings

proxy_url = settings.PROXY_URL or ""
print(f"Proxy: {proxy_url}")

if proxy_url:
    proxy_host = proxy_url.replace("http://", "").replace("https://", "").rsplit(":", 1)[0]
    proxy_port = int(proxy_url.rsplit(":", 1)[-1])
    http = httplib2.Http(
        timeout=15,
        proxy_info=httplib2.ProxyInfo(
            proxy_type=httplib2.socks.PROXY_TYPE_HTTP,
            proxy_host=proxy_host,
            proxy_port=proxy_port,
        )
    )
else:
    http = httplib2.Http(timeout=15)

url = "https://www.youtube.com/results?search_query=Midjourney+tutorial&sp=EgIQAg%3D%3D"
print(f"Fetching {url} ...")
resp, content = http.request(url, method="GET", headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
})
print(f"Status: {resp.status}")

html = content.decode("utf-8", errors="ignore")
match = re.search(r'var ytInitialData = ({.+?});</script>', html)
if match:
    data = json.loads(match.group(1))
    contents = data.get("contents", {}).get("twoColumnSearchResultsRenderer", {}).get("primaryContents", {}).get("sectionListRenderer", {}).get("contents", [])
    channels = []
    for section in contents:
        items = section.get("itemSectionRenderer", {}).get("contents", [])
        for item in items:
            ch = item.get("channelRenderer")
            if ch:
                channels.append({
                    "id": ch.get("channelId"),
                    "title": ch.get("title", {}).get("simpleText", ""),
                    "subs": ch.get("subscriberCountText", {}).get("simpleText", ""),
                })
    print(f"Found {len(channels)} channels")
    for c in channels[:5]:
        print(f"  {c['title'][:40]} | {c['id']} | {c['subs']}")
else:
    print("No ytInitialData found (可能是反爬页面)")
