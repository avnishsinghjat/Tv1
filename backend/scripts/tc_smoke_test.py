"""Optional smoke test against a running API (requires valid credentials)."""

from __future__ import annotations

import os
import sys

import httpx

BASE = (os.environ.get("TEAMCENTRE_API_BASE") or "").strip().rstrip("/")
USER = os.environ.get("TEAMCENTRE_USER", "admin")
PASS = os.environ.get("TEAMCENTRE_PASS", "admin")


def main() -> int:
    if not BASE:
        print("Set TEAMCENTRE_API_BASE to your analytics API origin (e.g. http://your-host:8000).", file=sys.stderr)
        return 2
    with httpx.Client(base_url=BASE, timeout=30.0) as client:
        r = client.get("/health")
        r.raise_for_status()
        print("health:", r.json())

        r = client.post("/api/auth/login", json={"username": USER, "password": PASS})
        r.raise_for_status()
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        r = client.post("/api/fetch/runs", json={"source_label": "smoke"}, headers=headers)
        r.raise_for_status()
        print("fetch run:", r.json())

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except httpx.HTTPError as exc:
        print("HTTP error:", exc, file=sys.stderr)
        raise SystemExit(1)
