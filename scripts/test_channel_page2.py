import httplib2, json, re, sys
sys.path.insert(0, r"D:\Projects\YouTube\tubefactory-ocp")
from apps.api.config import settings

proxy_url = settings.PROXY_URL or ""
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

channel_id = "UCldFPBqAVrok5DPUQeSMEqQ"
url = f"https://www.youtube.com/channel/{channel_id}/about"
resp, content = http.request(url, method="GET", headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
})

html = content.decode("utf-8", errors="ignore")
match = re.search(r'var ytInitialData = ({.+?});</script>', html)
data = json.loads(match.group(1))

# 打印关键路径
header = data.get("header", {})
print("Header keys:", header.keys())
if "c4TabbedHeaderRenderer" in header:
    c4 = header["c4TabbedHeaderRenderer"]
    print("c4 keys:", c4.keys())
    print("subscriberCountText:", c4.get("subscriberCountText"))

# 找视频数、观看量
for tab in data.get("contents", {}).get("twoColumnBrowseResultsRenderer", {}).get("tabs", []):
    if tab.get("tabRenderer", {}).get("title") == "About":
        content_sections = tab.get("tabRenderer", {}).get("content", {}).get("sectionListRenderer", {}).get("contents", [])
        for section in content_sections:
            items = section.get("itemSectionRenderer", {}).get("contents", [])
            for item in items:
                about = item.get("channelAboutFullMetadataRenderer", {})
                if about:
                    print("subscriberCountText:", about.get("subscriberCountText"))
                    print("videoCountText:", about.get("videoCountText"))
                    print("viewCountText:", about.get("viewCountText"))
                    print("joinedDateText:", about.get("joinedDateText"))
