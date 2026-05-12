"""Normalize external Teamcenter-style payloads into plain dicts."""

from __future__ import annotations

from typing import Any


def unwrap_envelope(body: Any) -> Any:
    """If the remote API wraps data in { 'data': ... }, unwrap it."""
    if isinstance(body, dict) and "data" in body and len(body) <= 5:
        return body.get("data")
    return body


def normalize_tc_record(raw: dict[str, Any]) -> dict[str, Any]:
    """Map common field spellings to columns used by `TCObject`."""
    srv = raw.get("serverInfo")
    if isinstance(srv, dict):
        uid = str(
            srv.get("UserID")
            or srv.get("userId")
            or raw.get("uid")
            or raw.get("UID")
            or ""
        )
        otype = str(raw.get("objectType") or raw.get("type") or "Teamcenter.ServerInfo")
        name = raw.get("name") or srv.get("HostName")
        rev = raw.get("revision") or srv.get("DisplayVersion") or srv.get("Version")
    else:
        uid = str(raw.get("uid") or raw.get("UID") or raw.get("objectUid") or "")
        otype = str(raw.get("objectType") or raw.get("type") or "Unknown")
        name = raw.get("name") or raw.get("object_name")
        rev = raw.get("revision") or raw.get("item_revision_id")

    src = raw.get("_tc_source")
    if isinstance(src, str) and (not uid or uid == "unknown"):
        uid = (uid or "unknown") + f"::{src}"
    return {
        "uid": (uid or "unknown")[:128],
        "object_type": otype[:128] if otype else "Unknown",
        "name": str(name)[:512] if name is not None else None,
        "revision": str(rev)[:64] if rev is not None else None,
        "payload": raw,
    }
