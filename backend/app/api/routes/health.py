"""Health check endpoint."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from app.config import settings
from app.services.cache_service import get_cache

router = APIRouter()


@router.get("/health", tags=["health"])
async def health() -> dict:
    cache = get_cache()
    return {
        "status": "ok",
        "service": settings.app_name,
        "env": settings.app_env,
        "mock_mode": settings.teamcenter_mock_mode,
        "redis_available": cache.available,
        "time": datetime.now(timezone.utc).isoformat(),
    }
