"""
网络探测工具 —— 自动发现可用代理 + 直连可用性测试

解决中国大陆用户 VPN 配置不确定性问题：
  - VPN 可能是 TUN 模式（无需代理配置）
  - VPN 可能是本地 HTTP 代理模式（需要配置端口）
  - VPN 可能未开启或端口不对

策略：
  1. 先测试直连 YouTube（3 秒超时）
  2. 如果直连不可用，扫描常见代理端口
  3. 返回最佳网络配置
"""
from __future__ import annotations

import asyncio
import logging
import socket
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# 常见代理端口（按流行度排序）
COMMON_PROXY_PORTS = [7890, 7897, 10808, 10809, 8080, 8118, 7070, 20171, 20172]

# 测试目标（Google / YouTube 的 HTTP 端点）
TEST_TARGETS = [
    "https://www.google.com/generate_204",
    "https://www.youtube.com",
]

# 缓存探测结果 + TTL（5 分钟），避免每次请求重复探测
_PROBE_CACHE: dict[str, Any] | None = None
_PROBE_CACHE_TIME: float = 0.0
_PROBE_TTL_SECONDS: float = 300.0
_probe_lock = asyncio.Lock()


async def _tcp_port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    """快速 TCP 端口探测."""
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout,
        )
        writer.close()
        await writer.wait_closed()
        return True
    except Exception:
        return False


async def _test_direct_connect(timeout: float = 3.0) -> bool:
    """测试能否直连 YouTube/Google（TUN 模式通常直接可用）."""
    for url in TEST_TARGETS:
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
                resp = await client.get(url)
                # 204 / 200 / 301/302 都表示网络可达
                if resp.status_code in (200, 204, 301, 302):
                    logger.info(f"Direct connection OK: {url} -> {resp.status_code}")
                    return True
        except Exception:
            continue
    logger.info("Direct connection to YouTube/Google failed")
    return False


async def _test_proxy(proxy_url: str, timeout: float = 3.0) -> bool:
    """测试代理是否可用."""
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=False,
            proxy=proxy_url,
        ) as client:
            resp = await client.get("https://www.google.com/generate_204")
            if resp.status_code in (200, 204, 301, 302):
                logger.info(f"Proxy OK: {proxy_url} -> {resp.status_code}")
                return True
    except Exception:
        pass
    return False


async def _discover_proxy() -> str | None:
    """自动发现本地代理端口."""
    for port in COMMON_PROXY_PORTS:
        # 先快速 TCP 探测，避免每个端口都发 HTTP 请求
        if not await _tcp_port_open("127.0.0.1", port, timeout=0.8):
            continue
        # TCP 通了，再发 HTTP 请求确认是 HTTP 代理
        for scheme in ("http://", "https://"):
            proxy_url = f"{scheme}127.0.0.1:{port}"
            if await _test_proxy(proxy_url, timeout=2.0):
                return proxy_url
    return None


async def probe_network(force: bool = False) -> dict[str, Any]:
    """
    探测最佳网络配置（线程安全 + 5 分钟 TTL）。

    Args:
        force: 强制重新探测，忽略缓存。

    Returns:
        {
            "direct_ok": bool,
            "proxy_url": str | None,
            "proxy_auto_detected": bool,
            "strategy": str,  # "direct" | "proxy" | "unavailable"
        }
    """
    global _PROBE_CACHE, _PROBE_CACHE_TIME
    now = time.monotonic()

    async with _probe_lock:
        if not force and _PROBE_CACHE is not None and (now - _PROBE_CACHE_TIME) < _PROBE_TTL_SECONDS:
            return _PROBE_CACHE

        # 1. 先测试直连
        direct_ok = await _test_direct_connect(timeout=3.0)

        if direct_ok:
            _PROBE_CACHE = {
                "direct_ok": True,
                "proxy_url": None,
                "proxy_auto_detected": False,
                "strategy": "direct",
            }
            _PROBE_CACHE_TIME = now
            logger.info("Network probe: direct connection available, no proxy needed")
            return _PROBE_CACHE

        # 2. 直连不可用，尝试发现代理
        discovered = await _discover_proxy()

        if discovered:
            _PROBE_CACHE = {
                "direct_ok": False,
                "proxy_url": discovered,
                "proxy_auto_detected": True,
                "strategy": "proxy",
            }
            _PROBE_CACHE_TIME = now
            logger.info(f"Network probe: using auto-discovered proxy {discovered}")
            return _PROBE_CACHE

        # 3. 都不行
        _PROBE_CACHE = {
            "direct_ok": False,
            "proxy_url": None,
            "proxy_auto_detected": False,
            "strategy": "unavailable",
        }
        _PROBE_CACHE_TIME = now
        logger.warning("Network probe: no working network path found")
        return _PROBE_CACHE


def get_effective_proxy_url(configured: str = "") -> str | None:
    """
    获取实际应使用的代理地址。

    优先级：
      1. 环境变量 / 配置中显式设置的 PROXY_URL
      2. 自动探测到的代理
      3. 无代理（直连）
    """
    if configured and configured.strip():
        return configured.strip()
    # 如果配置了但没生效，由调用方负责探测
    return None


def format_network_diagnosis(proxy_url: str | None, proxy_auto: bool, direct_ok: bool) -> str:
    """生成用户友好的网络诊断信息."""
    lines = []
    if direct_ok:
        lines.append("当前网络可直接访问 YouTube，无需代理。")
    elif proxy_url:
        lines.append(f"已通过代理 {proxy_url} 访问 YouTube。")
        if proxy_auto:
            lines.append("（代理为自动发现）")
    else:
        lines.append("无法连接到 YouTube，请检查：")
        lines.append("1. VPN 是否已开启")
        lines.append("2. 如果 VPN 是本地代理模式，确认端口是否正确")
        lines.append("3. 如果 VPN 是 TUN 模式，确保允许系统所有流量通过")
        lines.append("4. 在 .env 中手动设置 PROXY_URL=http://127.0.0.1:你的端口")
    return "\n".join(lines)
