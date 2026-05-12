"""Verify database connectivity (run from repo root: python backend/scripts/verify.py)."""

from __future__ import annotations

import sys
from pathlib import Path

backend_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_root))

from sqlalchemy import text

from app.database import engine


def main() -> int:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("database: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
