"""Teamcenter Active Workspace–style REST session login (Core-2011-06-Session).

Implements the flow visible in browser devtools: warmup request for cookies, then
POST to ``.../Core-2011-06-Session/login`` with JSON body + ``X-XSRF-TOKEN``.
"""

from __future__ import annotations

import uuid
from typing import Any

import httpx

from app.config import settings


def _login_payload(*, username: str, password: str) -> dict[str, Any]:
    """Body shape matches AWC login (see Network → Request JSON)."""
    d = settings.teamcenter_client_discriminator
    return {
        "body": {
            "credentials": {
                "descriminator": d,  # API spelling as used by Teamcenter
                "group": "",
                "locale": settings.teamcenter_locale,
                "password": password,
                "role": "",
                "user": username,
            }
        },
        "header": {
            "policy": {},
            "state": {
                "clientID": settings.teamcenter_client_id,
                "clientVersion": settings.teamcenter_client_version,
                "enableServerStateHeaders": True,
                "formatProperties": True,
                "logCorrelationID": "tc-middleware/1",
                "stateless": True,
                "unloadObjects": True,
            },
        },
    }


def _extra_headers() -> dict[str, str]:
    cid = str(uuid.uuid4())[:12]
    return {
        "Log-Correlation-ID": "tc-middleware/1",
        "x-siemens-operation-id": "tc-middleware/1",
        "x-siemens-session-id": cid,
        "x-correlation-id": cid,
    }


def _csrf_headers(client: httpx.AsyncClient) -> dict[str, str]:
    xsrf = client.cookies.get("XSRF-TOKEN")
    h: dict[str, str] = {"Accept": "application/json, text/plain, */*"}
    if xsrf:
        h["X-XSRF-TOKEN"] = xsrf
    return h


async def fetch_teamcenter_records() -> list[dict[str, Any]]:
    """
    Perform session login and turn the response into rows for persistence.

    Uses one ``httpx`` client so ``JSESSIONID`` / CSRF cookies stay on the session
    for any optional follow-up GETs (``TEAMCENTER_EXTRA_GET_PATHS``).
    """
    base = settings.teamcenter_base_url.rstrip("/")
    if not base:
        raise ValueError("TEAMCENTER_BASE_URL is not set")

    user = settings.teamcenter_user
    password = settings.teamcenter_password
    if not user or not password:
        raise ValueError("TEAMCENTER_USER and TEAMCENTER_PASSWORD must be set for live fetch")

    warmup_path = settings.teamcenter_warmup_path.strip() or "/tc/RestServices"
    login_path = settings.teamcenter_login_path.strip() or "/tc/RestServices/Core-2011-06-Session/login"
    if not warmup_path.startswith("/"):
        warmup_path = "/" + warmup_path
    if not login_path.startswith("/"):
        login_path = "/" + login_path

    rows: list[dict[str, Any]] = []
    extra_paths = settings.teamcenter_extra_get_paths

    async with httpx.AsyncClient(
        base_url=base,
        timeout=httpx.Timeout(120.0),
        follow_redirects=True,
    ) as client:
        await client.get(warmup_path)

        headers: dict[str, str] = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            **_extra_headers(),
            **_csrf_headers(client),
        }

        resp = await client.post(
            login_path,
            json=_login_payload(username=user, password=password),
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

        if isinstance(data, dict):
            rows.append({"_tc_source": "login_response", **data})
            srv = data.get("serverInfo")
            if isinstance(srv, dict):
                rows.append(
                    {
                        "_tc_source": "serverInfo",
                        "uid": str(srv.get("UserID") or srv.get("userId") or "unknown"),
                        "objectType": "Teamcenter.ServerInfo",
                        "name": srv.get("HostName"),
                        "revision": srv.get("DisplayVersion") or srv.get("Version"),
                        "serverInfo": srv,
                    }
                )

        for raw_path in extra_paths:
            path = raw_path.strip()
            if not path:
                continue
            if not path.startswith("/"):
                path = "/" + path
            r = await client.get(path, headers=_csrf_headers(client))
            r.raise_for_status()
            try:
                j = r.json()
            except Exception:  # noqa: BLE001
                j = {"_raw": r.text[:8000]}
            rows.append({"_tc_source": f"get:{path}", "data": j})

    return rows
