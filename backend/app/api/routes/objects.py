"""CRUD-style access to stored Teamcenter objects."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.tc_object import TCObject

router = APIRouter(prefix="/objects", tags=["objects"])


class TCObjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    fetch_run_id: uuid.UUID
    uid: str
    object_type: str
    name: str | None
    revision: str | None
    payload: dict[str, Any]
    created_at: datetime


@router.get("", response_model=list[TCObjectRead])
async def list_objects(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(get_current_user)],
    fetch_run_id: uuid.UUID | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[TCObject]:
    stmt = select(TCObject).order_by(TCObject.created_at.desc())
    if fetch_run_id is not None:
        stmt = stmt.where(TCObject.fetch_run_id == fetch_run_id)
    stmt = stmt.offset(max(offset, 0)).limit(min(limit, 500))
    return list(db.scalars(stmt))


@router.get("/{object_id}", response_model=TCObjectRead)
async def get_object(
    object_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(get_current_user)],
) -> TCObject:
    obj = db.get(TCObject, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Object not found")
    return obj
