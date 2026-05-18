"""
自动探测本机可用的 HTTP 代理端口
扫描常见代理软件默认端口，并测试是否能通过代理访问 YouTube
"""
import asyncio
import os
import socket
import sys
import urllib.request

COMMON_PROXY_PORTS = [7890, 7897, 1080, 10808, 10809, 8080, 8118, 8888, 8001, 8123]


def check_port(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        return True
    except Exception:
        return False


async def test_proxy_youtube(proxy_url: str, timeout: float = 8.0) -> bool:
    """测试代理是否能访问 YouTube."""
    try:
        proxy_handler = urllib.request.ProxyHandler({
            "http": proxy_url,
            "https": proxy_url,
        })
        opener = urllib.request.build_opener(proxy_handler)
        opener.addheaders = [("User-Agent", "Mozilla/5.0")]
        req = urllib.request.Request(
            "https://www.youtube.com",
            method="HEAD",
            headers={"User-Agent": "Mozilla/5.0"},
        )
        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: opener.open(req, timeout=timeout)
        )
        return response.getcode() == 200
    except Exception:
        return False


async def main():
    print("🔍 扫描本机代理端口...\n")

    # 1. 检查系统环境变量
    env_http = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    env_https = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if env_http or env_https:
        print(f"   系统环境变量代理: HTTP={env_http}, HTTPS={env_https}")
    else:
        print("   系统环境变量: 未设置代理")

    # 2. 扫描常见端口
    print("\n   扫描常见代理端口...")
    open_ports = []
    for port in COMMON_PROXY_PORTS:
        if check_port("127.0.0.1", port):
            open_ports.append(port)
            print(f"      ✅ 127.0.0.1:{port} 端口开放")

    if not open_ports:
        print("      ❌ 未发现开放端口")
        print("\n⚠️  你的代理软件可能没有开启「允许局域网连接」或「系统代理」")
        return 1

    # 3. 测试哪些端口能访问 YouTube
    print("\n   测试代理是否能访问 YouTube...")
    working_proxies = []
    for port in open_ports:
        proxy_url = f"http://127.0.0.1:{port}"
        ok = await test_proxy_youtube(proxy_url)
        if ok:
            working_proxies.append(proxy_url)
            print(f"      ✅ {proxy_url} → YouTube 可访问")
        else:
            print(f"      ❌ {proxy_url} → 无法访问 YouTube")

    print("\n" + "=" * 50)
    if working_proxies:
        print("🎉 找到可用代理:")
        for p in working_proxies:
            print(f"   PROXY_URL={p}")
        print(f"\n📋 请复制以下配置到 .env 文件:")
        print(f"   PROXY_URL={working_proxies[0]}")
        return 0
    else:
        print("❌ 端口开放但都无法访问 YouTube")
        print("\n可能原因:")
        print("   1. 代理软件没有开启「系统代理」或「TUN 模式」")
        print("   2. 代理软件规则中 YouTube 被排除")
        print("   3. 代理软件没有开启「允许局域网连接」")
        return 1


if __name__ == "__main__":
    code = asyncio.run(main())
    sys.exit(code)
