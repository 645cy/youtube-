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

# 测试多个频道
cids = ["UCldFPBqAVrok5DPUQeSMEqQ", "UC5OfgmpYlODuBfzUdqVPtHg", "UCuCAUf1zn_i0OKl9EUSM_LQ"]
for cid in cids:
    url = f"https://www.youtube.com/channel/{cid}/about"
    resp, content = http.request(url, method="GET", headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    html = content.decode("utf-8", errors="ignore")
    match = re.search(r'var ytInitialData = ({.+?});</script>', html)
    if not match:
        print(f"{cid}: no data")
        continue
    data = json.loads(match.group(1))
    
    # 尝试多种路径提取数据
    meta = data.get("metadata", {}).get("channelMetadataRenderer", {})
    title = meta.get("title", "")
    
    stats = {}
    for tab in data.get("contents", {}).get("twoColumnBrowseResultsRenderer", {}).get("tabs", []):
        about = tab.get("tabRenderer", {}).get("content", {}).get("sectionListRenderer", {}).get("contents", [])
        for section in about:
            items = section.get("itemSectionRenderer", {}).get("contents", [])
            for item in items:
                cam = item.get("channelAboutFullMetadataRenderer", {})
                if cam:
                    stats["subscriberCount"] = cam.get("subscriberCountText", {}).get("simpleText", "")
                    stats["videoCount"] = cam.get("videoCountText", {}).get("simpleText", "")
                    stats["viewCount"] = cam.get("viewCountText", {}).get("simpleText", "")
    
    print(f"{title[:30]:<30} | subs={stats.get('subscriberCount', 'N/A'):<12} | videos={stats.get('videoCount', 'N/A'):<10} | views={stats.get('viewCount', 'N/A')}")
    
    # 只打印第一个的完整结构用于调试
    if cid == cids[0]:
        print("  --- keys in channelAboutFullMetadataRenderer:", list(cam.keys()) if cam else "not found")
