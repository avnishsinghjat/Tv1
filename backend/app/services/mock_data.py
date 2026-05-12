"""Mock Teamcenter payloads for local development."""

from __future__ import annotations

from typing import Any


def sample_objects(source_label: str) -> list[dict[str, Any]]:
    return [
        {
            "uid": "0001",
            "objectType": "ItemRevision",
            "name": "Demo Assembly",
            "revision": "A",
            "attributes": {"item_id": "0001001", "source": source_label},
        },
        {
            "uid": "0002",
            "objectType": "ItemRevision",
            "name": "Demo Part",
            "revision": "B",
            "attributes": {"item_id": "0001002", "source": source_label},
        },
    ]
