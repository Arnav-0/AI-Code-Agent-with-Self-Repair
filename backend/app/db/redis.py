from __future__ import annotations

import json
import logging
from typing import Optional

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

_redis_manager: Optional["RedisManager"] = None


class RedisManager:
    def __init__(self, url: str) -> None:
        self.url = url
        self._pool: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        self._pool = aioredis.from_url(self.url, decode_responses=True)
        logger.info(f"Redis connected: {self.url}")

    async def disconnect(self) -> None:
        if self._pool is not None:
            await self._pool.aclose()
            self._pool = None
            logger.info("Redis disconnected")

    @property
    def pool(self) -> aioredis.Redis:
        if self._pool is None:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self._pool

    async def get(self, key: str) -> Optional[str]:
        return await self.pool.get(key)

    async def set(self, key: str, value: str, ttl: int = 3600) -> None:
        await self.pool.set(key, value, ex=ttl)

    async def delete(self, key: str) -> None:
        await self.pool.delete(key)

    async def get_json(self, key: str) -> Optional[dict]:
        value = await self.get(key)
        if value is None:
            return None
        return json.loads(value)

    async def set_json(self, key: str, value: dict, ttl: int = 3600) -> None:
        await self.set(key, json.dumps(value), ttl=ttl)

    async def publish(self, channel: str, message: str) -> None:
        await self.pool.publish(channel, message)


def get_redis_manager() -> Optional[RedisManager]:
    return _redis_manager


def init_redis_manager(url: str) -> RedisManager:
    global _redis_manager
    _redis_manager = RedisManager(url)
    return _redis_manager
