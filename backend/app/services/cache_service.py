"""Optional Redis cache used for Teamcenter response caching."""

from __future__ import annotations

from typing import Any

import redis

from app.config import settings
from app.utils.logger import get_logger

log = get_logger("cache")


class CacheService:
    def __init__(self) -> None:
        self._client: redis.Redis | None = None
        self._available = False
        if settings.redis_url:
            try:
                self._client = redis.from_url(settings.redis_url, decode_responses=True)
                self._client.ping()
                self._available = True
            except (redis.RedisError, OSError) as exc:
                log.warning("redis_unavailable", error=str(exc))
                self._client = None
                self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def get_json(self, key: str) -> Any | None:
        if not self._client:
            return None
        try:
            raw = self._client.get(key)
            if raw is None:
                return None
            import json

            return json.loads(raw)
        except (redis.RedisError, OSError, ValueError):
            return None

    def set_json(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        if not self._client:
            return
        import json

        try:
            self._client.setex(key, ttl_seconds, json.dumps(value))
        except (redis.RedisError, OSError, TypeError):
            pass


_cache: CacheService | None = None


def get_cache() -> CacheService:
    global _cache
    if _cache is None:
        _cache = CacheService()
    return _cache
