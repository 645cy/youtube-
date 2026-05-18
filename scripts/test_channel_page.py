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

# 测试抓频道详情页
channel_id = "UCldFPBqAVrok5DPUQeSMEqQ"  # Midjourney
url = f"https://www.youtube.com/channel/{channel_id}/about"
print(f"Fetching {url} ...")
resp, content = http.request(url, method="GET", headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
})
print(f"Status: {resp.status}")

html = content.decode("utf-8", errors="ignore")
match = re.search(r'var ytInitialData = ({.+?});</script>', html)
if match:
    data = json.loads(match.group(1))
    # 尝试提取订阅数、视频数、总观看量
    header = data.get("header", {}).get("c4TabbedHeaderRenderer", {})
    print(f"Title: {header.get('title', '')}")
    print(f"Subscribers: {header.get('subscriberCountText', {}).get('simpleText', '')}")
    
    # 从 metadata 提取
    meta = data.get("metadata", {}).get("channelMetadataRenderer", {})
    print(f"Description: {meta.get('description', '')[:100]}...")
    print(f"External ID: {meta.get('externalId', '')}")
else:
    print("No ytInitialData found")
