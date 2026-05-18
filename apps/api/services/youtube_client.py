from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def is_proxy_reachable(proxy_url: str, timeout: float = 3.0) -> bool:
    if not proxy_url:
        return False
    try:
        import socket

        host = proxy_url.replace("http://", "").replace("https://", "").rsplit(":", 1)[0]
        port_str = proxy_url.rsplit(":", 1)[-1]
        port = int(port_str) if port_str.isdigit() else 8080
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        return True
    except Exception:
        return False


class YouTubeAPIClient:
    def __init__(self, api_key: str | None = None, api_keys: list[str] | None = None, quota: Any | None = None) -> None:
        from apps.api.config import settings
        from apps.api.services.youtube_quota import KeyPoolManager, QuotaManager

        if api_keys:
            self._api_keys = api_keys
        elif api_key:
            self._api_keys = [k.strip() for k in api_key.split(",") if k.strip()]
        else:
            env_key = os.environ.get("YOUTUBE_API_KEY", "")
            self._api_keys = [k.strip() for k in env_key.split(",") if k.strip()] if env_key else settings.youtube_api_keys

        self._settings = settings
        self._proxy_initialized = False
        self._current_key_index = 0
        self._youtube = None

        if quota is None:
            if len(self._api_keys) > 1:
                state_dir = Path(settings.YOUTUBE_QUOTA_STATE_PATH).parent if settings.YOUTUBE_QUOTA_STATE_PATH else None
                self._key_pool = KeyPoolManager(self._api_keys, settings.API_QUOTA_LIMIT, str(state_dir) if state_dir else None)
                self._quota = None
            else:
                self._quota = QuotaManager(settings.API_QUOTA_LIMIT, settings.YOUTUBE_QUOTA_STATE_PATH)
                self._key_pool = None
        else:
            self._key_pool = quota if hasattr(quota, "get_best_key") else None
            self._quota = quota if not self._key_pool else None

        if self._api_keys:
            self._build_youtube(0)

    def _build_youtube(self, index: int) -> bool:
        if index < 0 or index >= len(self._api_keys):
            return False
        try:
            from googleapiclient.discovery import build
            import httplib2

            http = httplib2.Http()
            proxy_url = self._settings.PROXY_URL or os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
            if proxy_url:
                proxy_host = proxy_url.replace("http://", "").replace("https://", "").rsplit(":", 1)[0]
                proxy_port_str = proxy_url.rsplit(":", 1)[-1]
                try:
                    proxy_port = int(proxy_port_str)
                except ValueError:
                    proxy_port = 8080
                http = httplib2.Http(timeout=10, proxy_info=httplib2.ProxyInfo(proxy_type=httplib2.socks.PROXY_TYPE_HTTP, proxy_host=proxy_host, proxy_port=proxy_port))
            self._youtube = build("youtube", "v3", developerKey=self._api_keys[index], http=http, cache_discovery=False)
            self._current_key_index = index
            return True
        except ImportError:
            logger.warning("google-api-python-client not installed, API mode unavailable")
            return False

    async def _ensure_proxy(self) -> None:
        if self._proxy_initialized:
            return
        self._proxy_initialized = True
        if self._settings.PROXY_URL:
            if is_proxy_reachable(self._settings.PROXY_URL):
                self._apply_proxy_to_build(self._settings.PROXY_URL)

    def _apply_proxy_to_build(self, proxy_url: str) -> None:
        if not self._youtube:
            return
        try:
            import httplib2

            proxy_host = proxy_url.replace("http://", "").replace("https://", "").rsplit(":", 1)[0]
            proxy_port_str = proxy_url.rsplit(":", 1)[-1]
            try:
                proxy_port = int(proxy_port_str)
            except ValueError:
                proxy_port = 8080
            http = httplib2.Http(proxy_info=httplib2.ProxyInfo(proxy_type=httplib2.socks.PROXY_TYPE_HTTP, proxy_host=proxy_host, proxy_port=proxy_port))
            self._youtube._http = http  # type: ignore[attr-defined]
        except Exception:
            logger.exception("Failed to apply proxy")
