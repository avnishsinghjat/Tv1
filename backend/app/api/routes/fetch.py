"""Trigger and inspect Teamcenter fetch runs."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models.tc_object import FetchRun, TCObject
from app.services.cache_service import get_cache
from app.services.mock_data import sample_objects
from app.services.tc_envelope import normalize_tc_record, unwrap_envelope
from app.services.tc_rest_client import fetch_teamcenter_records

router = APIRouter(prefix="/fetch", tags=["fetch"])


class FetchCreate(BaseModel):
    source_label: str | None = Field(default=None, max_length=256)
    use_cache: bool = True


class FetchRunSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    source_label: str | None
    objects_count: int
    created_at: datetime
    completed_at: datetime | None
    error_message: str | None


def _cache_key(label: str) -> str:
    return f"tc:fetch:{label}"


@router.post("/runs", response_model=FetchRunSummary)
async def create_fetch_run(
    body: FetchCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(get_current_user)],
) -> FetchRun:
    run = FetchRun(status="running", source_label=body.source_label)
    db.add(run)
    db.commit()
    db.refresh(run)

    label = body.source_label or "default"
    cache = get_cache()

    try:
        records: list[dict[str, Any]] = []
        if settings.teamcenter_mock_mode:
            records = sample_objects(label)
        elif body.use_cache and cache.available:
            cached = cache.get_json(_cache_key(label))
            if cached is not None:
                unwrapped = unwrap_envelope(cached)
                if isinstance(unwrapped, list):
                    records = [r for r in unwrapped if isinstance(r, dict)]
                elif isinstance(unwrapped, dict):
                    records = [unwrapped]

        if not records and not settings.teamcenter_mock_mode:
            if not settings.teamcenter_base_url.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="TEAMCENTER_BASE_URL is not configured",
                )
            try:
                records = await fetch_teamcenter_records()
            except httpx.HTTPStatusError as exc:
                detail = exc.response.text[:2000] if exc.response else str(exc)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Teamcenter HTTP error: {detail}",
                ) from exc
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(exc),
                ) from exc

        for raw in records:
            normalized = normalize_tc_record(raw)
            db.add(
                TCObject(
                    fetch_run_id=run.id,
                    uid=normalized["uid"],
                    object_type=normalized["object_type"],
                    name=normalized["name"],
                    revision=normalized["revision"],
                    payload=normalized["payload"],
                )
            )

        if settings.teamcenter_mock_mode and body.use_cache and cache.available:
            cache.set_json(_cache_key(label), records)

        run.status = "completed"
        run.objects_count = len(records)
        run.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(run)
        return run
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        failed = db.get(FetchRun, run.id)
        if failed:
            failed.status = "failed"
            failed.error_message = str(exc)
            failed.completed_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(failed)
            return failed
        raise


@router.get("/runs", response_model=list[FetchRunSummary])
async def list_fetch_runs(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(get_current_user)],
    limit: int = 50,
) -> list[FetchRun]:
    stmt = select(FetchRun).order_by(FetchRun.created_at.desc()).limit(min(limit, 200))
    return list(db.scalars(stmt))


@router.get("/runs/{run_id}", response_model=FetchRunSummary)
async def get_fetch_run(
    run_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(get_current_user)],
) -> FetchRun:
    run = db.get(FetchRun, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return run
