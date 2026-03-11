from __future__ import annotations

from typing import Optional

from app.db.redis import RedisManager

SETTINGS_CACHE_KEY = "codeforge:settings"
TASK_STATUS_KEY_PREFIX = "codeforge:task_status:"


class CacheService:
    def __init__(self, redis: RedisManager) -> None:
        self.redis = redis

    async def cache_settings(self, settings: dict) -> None:
        await self.redis.set_json(SETTINGS_CACHE_KEY, settings, ttl=3600)

    async def get_cached_settings(self) -> Optional[dict]:
        return await self.redis.get_json(SETTINGS_CACHE_KEY)

    async def invalidate_settings(self) -> None:
        await self.redis.delete(SETTINGS_CACHE_KEY)

    async def cache_task_status(self, task_id: str, status: str) -> None:
        await self.redis.set(
            f"{TASK_STATUS_KEY_PREFIX}{task_id}", status, ttl=86400
        )

    async def get_cached_task_status(self, task_id: str) -> Optional[str]:
        return await self.redis.get(f"{TASK_STATUS_KEY_PREFIX}{task_id}")
