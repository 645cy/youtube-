from __future__ import annotations

import asyncio
import socket
from concurrent.futures import ThreadPoolExecutor

from apps.api.config import settings

_blocking_executor: ThreadPoolExecutor | None = None


def is_proxy_reachable(proxy_url: str, timeout: float = 3.0) -> bool:
    if not proxy_url:
        return False
    try:
        host = proxy_url.replace("http://", "").replace("https://", "").rsplit(":", 1)[0]
        port_str = proxy_url.rsplit(":", 1)[-1]
        port = int(port_str) if port_str.isdigit() else 8080
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        return True
    except Exception:
        return False


def get_blocking_executor() -> ThreadPoolExecutor:
    global _blocking_executor
    if _blocking_executor is None:
        _blocking_executor = ThreadPoolExecutor(
            max_workers=max(1, settings.YOUTUBE_BLOCKING_MAX_WORKERS),
            thread_name_prefix="youtube-blocking",
        )
    return _blocking_executor


def close_youtube_executor() -> None:
    global _blocking_executor
    if _blocking_executor is not None:
        _blocking_executor.shutdown(wait=False, cancel_futures=True)
        _blocking_executor = None
