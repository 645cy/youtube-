"""
统一爬虫调度引擎

核心组件:
  1. AdaptiveBackoff: 自适应指数退避 + Jitter (应对 429/503)
  2. SlidingWindowRateLimiter: 滑动窗口限速器
  3. ProxyPool: 代理池管理 (静态列表 + 失败追踪)
  4. CrawlerEngine: 统一调度引擎 (调度、限流、队列、UA轮换)

反爬策略矩阵:
  - 随机请求间隔: 1.5s - 4.5s
  - User-Agent 轮换: 5 种主流浏览器
  - 429 指数退避: base=2s, max=60s, max_retries=5
  - 滑动窗口限速: 15 req/min
  - Cookie 持久化: 模拟会话连续性
"""
from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

import httpx

logger = logging.getLogger("crawler")


# ── 配置 ──

@dataclass(slots=True, frozen=True)
class CrawlerPolicy:
    """爬虫行为策略配置 (不可变)."""
    min_delay_ms: int = 1_500
    max_delay_ms: int = 4_500
    randomize_delay: bool = True
    backoff_base_delay: float = 2.0
    backoff_max_delay: float = 60.0
    backoff_jitter_ratio: float = 0.3
    max_retries: int = 5
    proxy_rotation_strategy: Literal["per_request", "on_error", "sticky"] = "per_request"
    user_agent_rotation: bool = True
    custom_user_agents: list[str] = field(default_factory=list)
    connect_timeout: float = 10.0
    read_timeout: float = 30.0
    max_concurrency: int = 3
    max_requests_per_minute: int = 15


# ── User-Agent 轮换 ──

DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
]


class UserAgentRotator:
    """User-Agent 轮换器."""

    def __init__(self, custom_agents: list[str] | None = None) -> None:
        self._agents = custom_agents or DEFAULT_USER_AGENTS
        self._index = 0

    def get_random(self) -> str:
        return random.choice(self._agents)

    def get_next(self) -> str:
        ua = self._agents[self._index % len(self._agents)]
        self._index += 1
        return ua


# ── 代理池 ──

class ProxyProvider(Protocol):
    """代理提供者协议."""
    async def get_proxy(self, failed_proxy: str | None = None) -> str | None: ...
    async def report_failure(self, proxy: str) -> None: ...


class ProxyPool:
    """静态代理池 (支持失败追踪与自动轮换)."""

    def __init__(self, proxies: list[str]) -> None:
        self._proxies = proxies
        self._failed: set[str] = set()
        self._lock = asyncio.Lock()

    async def get_proxy(self, failed_proxy: str | None = None) -> str | None:
        async with self._lock:
            if failed_proxy:
                self._failed.add(failed_proxy)
            available = [p for p in self._proxies if p not in self._failed]
            if not available:
                return None
            return random.choice(available)

    async def report_failure(self, proxy: str) -> None:
        async with self._lock:
            self._failed.add(proxy)

    def reset_failures(self) -> None:
        self._failed.clear()


# ── 自适应退避 ──

class AdaptiveBackoff:
    """自适应指数退避 + 全抖动 (Full Jitter).

    算法: sleep = min(max_delay, base * 2^attempt) + jitter
    参考: AWS Architecture Blog — Exponential Backoff and Jitter
    """

    def __init__(
        self,
        base_delay: float = 2.0,
        max_delay: float = 60.0,
        jitter_ratio: float = 0.3,
        max_retries: int = 5,
    ) -> None:
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter_ratio = jitter_ratio
        self.max_retries = max_retries

    def calculate(self, attempt: int, retry_after: float | None = None) -> float:
        if retry_after is not None and retry_after > 0:
            jitter = random.uniform(0, retry_after * self.jitter_ratio)
            return retry_after + jitter

        exponential = min(self.max_delay, self.base_delay * (2 ** attempt))
        jitter = random.uniform(0, exponential * self.jitter_ratio)
        return exponential + jitter

    async def sleep(self, attempt: int, retry_after: float | None = None) -> float:
        duration = self.calculate(attempt, retry_after)
        logger.warning(f"Backoff attempt {attempt + 1}/{self.max_retries}: sleeping {duration:.2f}s")
        await asyncio.sleep(duration)
        return duration

    def should_retry(self, attempt: int, status_code: int | None = None) -> bool:
        if attempt >= self.max_retries:
            return False
        if status_code and status_code not in (429, 500, 502, 503, 504):
            return False
        return True


# ── 滑动窗口限速器 ──

class SlidingWindowRateLimiter:
    """滑动窗口速率限制器 (限制每分钟最大请求数)."""

    def __init__(self, max_requests: int = 15, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._timestamps: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """获取发送请求的许可, 必要时等待."""
        async with self._lock:
            now = time.monotonic()
            # 清理过期记录
            cutoff = now - self.window_seconds
            self._timestamps = [ts for ts in self._timestamps if ts > cutoff]

            if len(self._timestamps) >= self.max_requests:
                oldest = self._timestamps[0]
                wait_time = self.window_seconds - (now - oldest) + 0.5
                if wait_time > 0:
                    logger.info(f"Rate limit: waiting {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)

            self._timestamps.append(time.monotonic())


# ── 统一调度引擎 ──

class CrawlerEngine:
    """生产级异步爬虫引擎.

    集成:
      - 随机请求间隔
      - UA 轮换
      - 代理池轮换
      - 429 指数退避 + Jitter
      - 滑动窗口速率限制
      - Cookie 持久化
    """

    def __init__(
        self,
        policy: CrawlerPolicy | None = None,
        proxy_pool: ProxyPool | None = None,
    ) -> None:
        self.policy = policy or CrawlerPolicy()
        self.ua_rotator = UserAgentRotator(self.policy.custom_user_agents)
        self.backoff = AdaptiveBackoff(
            base_delay=self.policy.backoff_base_delay,
            max_delay=self.policy.backoff_max_delay,
            jitter_ratio=self.policy.backoff_jitter_ratio,
            max_retries=self.policy.max_retries,
        )
        self.rate_limiter = SlidingWindowRateLimiter(
            max_requests=self.policy.max_requests_per_minute,
        )
        self.proxy_pool = proxy_pool

        self._cookie_jar = httpx.Cookies()
        self._current_proxy: str | None = None
        self._semaphore = asyncio.Semaphore(self.policy.max_concurrency)
        self._request_count = 0
        self._error_count = 0
        self._retry_count = 0

    def _build_headers(self) -> dict[str, str]:
        ua = (
            self.ua_rotator.get_random()
            if self.policy.user_agent_rotation
            else DEFAULT_USER_AGENTS[0]
        )
        return {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": random.choice(["en-US,en;q=0.9", "en-GB,en;q=0.9"]),
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": random.choice([
                "https://www.google.com/",
                "https://www.youtube.com/",
            ]),
            "DNT": "1",
            "Connection": "keep-alive",
        }

    async def _get_proxy(self, force_new: bool = False) -> str | None:
        if not self.proxy_pool:
            return None
        if self.policy.proxy_rotation_strategy == "sticky" and self._current_proxy and not force_new:
            return self._current_proxy
        proxy = await self.proxy_pool.get_proxy(
            failed_proxy=self._current_proxy if force_new else None
        )
        self._current_proxy = proxy
        return proxy

    async def request(
        self,
        method: Literal["GET", "POST"],
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """执行 HTTP 请求 (带完整反爬策略)."""
        async with self._semaphore:
            # 请求间隔
            if self.policy.randomize_delay:
                delay = random.randint(self.policy.min_delay_ms, self.policy.max_delay_ms) / 1000
                await asyncio.sleep(delay)

            # 限速
            await self.rate_limiter.acquire()

            attempt = 0
            while True:
                headers = {**self._build_headers(), **kwargs.pop("headers", {})}
                proxy = await self._get_proxy(force_new=(attempt > 0))

                try:
                    timeout = httpx.Timeout(
                        self.policy.read_timeout,
                        connect=self.policy.connect_timeout,
                    )
                    proxies = {"http://": proxy, "https://": proxy} if proxy else None
                    async with httpx.AsyncClient(
                        proxies=proxies,
                        timeout=timeout,
                        cookies=self._cookie_jar,
                        follow_redirects=True,
                    ) as client:
                        response = await client.request(method, url, headers=headers, **kwargs)

                    self._cookie_jar.update(response.cookies)
                    self._request_count += 1

                    # 429/503 处理
                    if response.status_code in (429, 503):
                        self._error_count += 1
                        retry_after = response.headers.get("Retry-After")
                        retry_after_float = float(retry_after) if retry_after else None

                        if self.backoff.should_retry(attempt, response.status_code):
                            await self.backoff.sleep(attempt, retry_after_float)
                            attempt += 1
                            self._retry_count += 1
                            continue
                        else:
                            response.raise_for_status()

                    return response

                except httpx.HTTPStatusError:
                    raise
                except Exception:
                    self._error_count += 1
                    if self.backoff.should_retry(attempt):
                        await self.backoff.sleep(attempt)
                        attempt += 1
                        self._retry_count += 1
                        continue
                    raise

    async def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("POST", url, **kwargs)

    def get_stats(self) -> dict[str, Any]:
        """获取爬虫统计."""
        return {
            "requests_total": self._request_count,
            "errors_total": self._error_count,
            "retries_total": self._retry_count,
            "proxies_available": len(self.proxy_pool._proxies) - len(self.proxy_pool._failed) if self.proxy_pool else 0,
        }

    async def close(self) -> None:
        """清理资源."""
        self._cookie_jar.clear()
