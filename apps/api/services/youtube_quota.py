from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class EndpointCost(Enum):
    SEARCH_LIST = 100
    VIDEOS_LIST = 1
    CHANNELS_LIST = 1
    PLAYLISTITEMS_LIST = 1
    COMMENTTHREADS_LIST = 1
    ACTIVITIES_LIST = 1


@dataclass(slots=True)
class QuotaSnapshot:
    units_consumed: int = 0
    units_remaining: int = 10000
    last_reset_utc: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    call_log: list[tuple[datetime, str, int]] = field(default_factory=list)

    def with_call(self, endpoint: str, cost: int) -> QuotaSnapshot:
        now = datetime.now(timezone.utc)
        return QuotaSnapshot(
            units_consumed=self.units_consumed + cost,
            units_remaining=max(0, self.units_remaining - cost),
            last_reset_utc=self.last_reset_utc,
            call_log=self.call_log + [(now, endpoint, cost)],
        )

    def is_exhausted(self, buffer: int = 50) -> bool:
        return self.units_remaining <= buffer

    def reset_if_needed(self, daily_quota: int = 10000) -> QuotaSnapshot:
        now_utc = datetime.now(timezone.utc)
        pt_offset = timedelta(hours=7 if hasattr(__import__("time"), "daylight") and __import__("time").daylight else 8)
        now_pt = now_utc - pt_offset
        reset_pt = self.last_reset_utc - pt_offset
        if now_pt.date() != reset_pt.date():
            return QuotaSnapshot(units_consumed=0, units_remaining=daily_quota, last_reset_utc=now_utc, call_log=[])
        return self


class QuotaManager:
    DEFAULT_DAILY_QUOTA = 10_000

    def __init__(self, daily_quota: int = DEFAULT_DAILY_QUOTA, state_path: str | None = None) -> None:
        self._daily_quota = daily_quota
        self._state_path = Path(state_path) if state_path else None
        self._snapshot = self._load_snapshot() or QuotaSnapshot(
            units_consumed=0, units_remaining=daily_quota, last_reset_utc=datetime.now(timezone.utc), call_log=[]
        )
        self._lock = asyncio.Lock()

    @property
    def snapshot(self) -> QuotaSnapshot:
        snap = self._snapshot.reset_if_needed(self._daily_quota)
        if snap != self._snapshot:
            self._snapshot = snap
            self._persist_snapshot()
        return self._snapshot

    def _load_snapshot(self) -> QuotaSnapshot | None:
        if not self._state_path or not self._state_path.exists():
            return None
        try:
            data = json.loads(self._state_path.read_text(encoding="utf-8"))
            return QuotaSnapshot(
                units_consumed=int(data.get("units_consumed", 0)),
                units_remaining=int(data.get("units_remaining", self._daily_quota)),
                last_reset_utc=datetime.fromisoformat(data["last_reset_utc"]),
                call_log=[(datetime.fromisoformat(ts), str(ep), int(cost)) for ts, ep, cost in data.get("call_log", [])],
            )
        except Exception as e:
            logger.warning("Quota state ignored because it could not be loaded: %s", e)
            return None

    def _persist_snapshot(self) -> None:
        if not self._state_path:
            return
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "units_consumed": self._snapshot.units_consumed,
            "units_remaining": self._snapshot.units_remaining,
            "last_reset_utc": self._snapshot.last_reset_utc.isoformat(),
            "call_log": [(ts.isoformat(), ep, cost) for ts, ep, cost in self._snapshot.call_log[-500:]],
        }
        self._state_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    async def record(self, endpoint: EndpointCost | str, cost: int | None = None) -> None:
        async with self._lock:
            if isinstance(endpoint, EndpointCost):
                name, cost = endpoint.name, endpoint.value
            else:
                name = endpoint
                cost = cost or 1
            self._snapshot = self._snapshot.with_call(name, cost)
            self._persist_snapshot()

    async def check_budget(self, needed: int = 1) -> bool:
        return not self.snapshot.is_exhausted(buffer=needed)

    async def get_usage_report(self) -> dict[str, Any]:
        snap = self.snapshot
        endpoint_totals: dict[str, int] = {}
        for _, ep, cost in snap.call_log:
            endpoint_totals[ep] = endpoint_totals.get(ep, 0) + cost
        return {
            "units_consumed": snap.units_consumed,
            "units_remaining": snap.units_remaining,
            "usage_pct": round(snap.units_consumed / self._daily_quota * 100, 2),
            "endpoints": endpoint_totals,
            "calls_total": len(snap.call_log),
            "next_reset_pt": "Midnight Pacific Time",
        }


class KeyPoolManager:
    def __init__(self, api_keys: list[str], daily_quota: int = 10_000, state_dir: str | None = None) -> None:
        self._api_keys = api_keys
        self._daily_quota = daily_quota
        self._state_dir = Path(state_dir) if state_dir else None
        self._snapshots: dict[int, QuotaSnapshot] = {}
        self._key_health: dict[int, bool] = {}
        self._lock = asyncio.Lock()
        self._load_all()

    def _state_path(self, index: int) -> Path:
        if not self._state_dir:
            return Path("/dev/null")
        if len(self._api_keys) == 1:
            return self._state_dir / "youtube_quota_state.json"
        return self._state_dir / f"youtube_quota_state_{index}.json"

    def _load_all(self) -> None:
        for i in range(len(self._api_keys)):
            self._snapshots[i] = self._load_snapshot(i)
            self._key_health[i] = True

    def _load_snapshot(self, index: int) -> QuotaSnapshot:
        path = self._state_path(index)
        if not path.exists():
            return QuotaSnapshot(units_consumed=0, units_remaining=self._daily_quota, last_reset_utc=datetime.now(timezone.utc), call_log=[])
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            snap = QuotaSnapshot(
                units_consumed=int(data.get("units_consumed", 0)),
                units_remaining=int(data.get("units_remaining", self._daily_quota)),
                last_reset_utc=datetime.fromisoformat(data["last_reset_utc"]),
                call_log=[(datetime.fromisoformat(ts), str(ep), int(cost)) for ts, ep, cost in data.get("call_log", [])],
            )
            return snap.reset_if_needed(self._daily_quota)
        except Exception as e:
            logger.warning("Quota state load failed for key %s: %s", index, e)
            return QuotaSnapshot(units_consumed=0, units_remaining=self._daily_quota, last_reset_utc=datetime.now(timezone.utc), call_log=[])

    def _persist_snapshot(self, index: int) -> None:
        if not self._state_dir:
            return
        path = self._state_path(index)
        snap = self._snapshots[index]
        payload = {
            "units_consumed": snap.units_consumed,
            "units_remaining": snap.units_remaining,
            "last_reset_utc": snap.last_reset_utc.isoformat(),
            "call_log": [(ts.isoformat(), ep, cost) for ts, ep, cost in snap.call_log[-500:]],
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    async def get_best_key(self) -> tuple[int, str] | tuple[None, None]:
        async with self._lock:
            candidates: list[tuple[int, int, str]] = []
            for i, key in enumerate(self._api_keys):
                if not self._key_health.get(i, True):
                    continue
                snap = self._snapshots[i].reset_if_needed(self._daily_quota)
                if snap != self._snapshots[i]:
                    self._snapshots[i] = snap
                    self._persist_snapshot(i)
                if not snap.is_exhausted():
                    candidates.append((snap.units_remaining, i, key))
            if not candidates:
                return None, None
            candidates.sort(reverse=True)
            return candidates[0][1], candidates[0][2]

    async def record(self, index: int, endpoint: EndpointCost | str, cost: int | None = None) -> None:
        async with self._lock:
            if isinstance(endpoint, EndpointCost):
                name, cost = endpoint.name, endpoint.value
            else:
                name = endpoint
                cost = cost or 1
            self._snapshots[index] = self._snapshots[index].with_call(name, cost)
            self._persist_snapshot(index)

    async def check_budget(self, index: int, needed: int = 1) -> bool:
        snap = self._snapshots[index].reset_if_needed(self._daily_quota)
        if snap != self._snapshots[index]:
            self._snapshots[index] = snap
            self._persist_snapshot(index)
        return not snap.is_exhausted(buffer=needed)

    async def mark_key_bad(self, index: int) -> None:
        async with self._lock:
            self._key_health[index] = False
            logger.warning("API key %s marked as bad (quota exhausted or 403)", index)

    async def get_usage_report(self) -> dict[str, Any]:
        total_consumed = 0
        total_remaining = 0
        key_reports = []
        for i, key in enumerate(self._api_keys):
            snap = self._snapshots[i].reset_if_needed(self._daily_quota)
            total_consumed += snap.units_consumed
            total_remaining += snap.units_remaining
            masked = key[:6] + "..." + key[-4:] if len(key) > 12 else "***"
            key_reports.append({
                "index": i,
                "key_masked": masked,
                "healthy": self._key_health.get(i, True),
                "units_consumed": snap.units_consumed,
                "units_remaining": snap.units_remaining,
            })
        return {
            "keys_total": len(self._api_keys),
            "keys_healthy": sum(1 for h in self._key_health.values() if h),
            "units_consumed": total_consumed,
            "units_remaining": total_remaining,
            "daily_quota_total": len(self._api_keys) * self._daily_quota,
            "keys": key_reports,
        }
