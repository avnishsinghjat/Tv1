"""Sync database tables from SQLAlchemy models (dev helper, similar to Prisma `db push`).

Creates missing tables; does not drop columns or run destructive migrations.
Run from repo root with Docker:

  docker compose run --rm db-push

Or locally (backend on PYTHONPATH, DATABASE_URL set):

  cd backend && set PYTHONPATH=. && py -3 scripts/db_push.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Running as `python scripts/db_push.py` puts `scripts/` on sys.path; ensure backend root is importable.
_backend_root = Path(__file__).resolve().parents[1]
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from app.database import Base, engine

# Ensure model metadata is registered on Base
from app.models import FetchRun, TCObject  # noqa: F401
from app.schema_fixup import quarantine_legacy_tc_objects_table


def main() -> None:
    quarantine_legacy_tc_objects_table(engine)
    Base.metadata.create_all(bind=engine)
    print("db-push: schema synced (create_all).")


if __name__ == "__main__":
    main()
