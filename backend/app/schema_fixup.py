"""Best-effort handling when an older tc_objects layout is in the database.

`Base.metadata.create_all` does not alter existing tables. If a legacy `tc_objects`
table (no ``fetch_run_id``) is present, we rename it so ``create_all`` can create
the current schema.

On PostgreSQL, renaming the table leaves index and constraint names unchanged; those
names must stay unique within the schema, so we rename them too. A half-applied
migration (table already renamed away) is repaired by renaming artifacts on
``tc_objects_legacy_%`` tables before ``create_all``.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection
from sqlalchemy.engine import Engine

from app.utils.logger import get_logger

log = get_logger("schema_fixup")

_PG_ID_MAX = 63

# Default index/constraint names from the current ORM model (must not be taken by a legacy table).
_CONFLICTING_ARTIFACT_NAMES = frozenset(
    {
        "tc_objects_pkey",
        "ix_tc_objects_uid",
        "ix_tc_objects_object_type",
        "ix_tc_objects_fetch_run_id",
    }
)


def _tag_from_legacy_table(table: str) -> str:
    prefix = "tc_objects_legacy_"
    if table.startswith(prefix):
        return f"l_{table[len(prefix) :]}"
    return f"l_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"


def _pg_ident(base: str, tag: str) -> str:
    s = f"{base}_{tag}"
    return s[:_PG_ID_MAX]


def _pg_rename_table_artifacts(conn: Connection, table: str, tag: str) -> None:
    con_rows = conn.execute(
        text(
            """
            SELECT c.conname
            FROM pg_constraint c
            JOIN pg_class cl ON cl.oid = c.conrelid
            JOIN pg_namespace n ON n.oid = cl.relnamespace
            WHERE n.nspname = 'public' AND cl.relname = :t
            ORDER BY c.conname
            """
        ),
        {"t": table},
    ).fetchall()
    for (conname,) in con_rows:
        conn.execute(
            text(f'ALTER TABLE "{table}" RENAME CONSTRAINT "{conname}" TO "{_pg_ident(conname, tag)}"')
        )

    ix_rows = conn.execute(
        text(
            """
            SELECT indexname FROM pg_indexes
            WHERE schemaname = 'public' AND tablename = :t
            ORDER BY indexname
            """
        ),
        {"t": table},
    ).fetchall()
    for (ix_name,) in ix_rows:
        conn.execute(text(f'ALTER INDEX "{ix_name}" RENAME TO "{_pg_ident(ix_name, tag)}"'))


def _repair_half_applied_pg_migration(engine: Engine) -> None:
    insp = inspect(engine)
    if insp.has_table("tc_objects"):
        return
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT DISTINCT tablename
                FROM pg_indexes
                WHERE schemaname = 'public'
                  AND tablename ~ '^tc_objects_legacy_'
                  AND indexname = ANY(:names)
                """
            ),
            {"names": list(_CONFLICTING_ARTIFACT_NAMES)},
        ).fetchall()
        for (tname,) in rows:
            tag = _tag_from_legacy_table(tname)
            _pg_rename_table_artifacts(conn, tname, tag)
            log.warning("legacy_tc_objects_artifacts_renamed", preserved_table=tname)


def quarantine_legacy_tc_objects_table(engine: Engine) -> None:
    """Rename pre-ORM tc_objects (and related PG names) so the ORM can create the table."""
    if engine.dialect.name == "postgresql":
        _repair_half_applied_pg_migration(engine)

    insp = inspect(engine)
    if not insp.has_table("tc_objects"):
        return
    columns = {c["name"] for c in insp.get_columns("tc_objects")}
    if "fetch_run_id" in columns:
        return

    suffix = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    new_name = f"tc_objects_legacy_{suffix}"
    tag = _tag_from_legacy_table(new_name)

    with engine.begin() as conn:
        conn.execute(text(f'ALTER TABLE tc_objects RENAME TO "{new_name}"'))
        if engine.dialect.name == "postgresql":
            _pg_rename_table_artifacts(conn, new_name, tag)
    log.warning("legacy_tc_objects_renamed", preserved_table=new_name)
