from __future__ import annotations

import os
import time
import urllib.request


BASE_URL = os.getenv("TUBEFACTORY_FRONTEND_BASE_URL", "http://127.0.0.1:3000").rstrip("/")
STARTUP_WAIT_SECONDS = int(os.getenv("TUBEFACTORY_FRONTEND_WAIT_SECONDS", "5"))
PAGES = ["/dashboard", "/radar", "/crawler", "/lab", "/factory"]


def main() -> int:
    if STARTUP_WAIT_SECONDS > 0:
        print(f"Waiting for frontend startup: {STARTUP_WAIT_SECONDS}s")
        time.sleep(STARTUP_WAIT_SECONDS)

    failed = 0
    for path in PAGES:
        url = f"{BASE_URL}{path}"
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                html = response.read().decode("utf-8", "ignore")
            has_main = "main" in html.lower()
            has_next = "__next" in html
            status = "OK" if response.status == 200 and (has_main or has_next) else "WARN"
            print(f"{status} {path}: HTTP {response.status}, main={has_main}, next={has_next}")
            if status != "OK":
                failed += 1
        except Exception as exc:
            print(f"FAIL {path}: {str(exc)[:120]}")
            failed += 1
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
