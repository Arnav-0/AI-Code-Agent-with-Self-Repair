from __future__ import annotations

import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


async def _check_database() -> str:
    try:
        from sqlalchemy import text

        from app.db.session import async_session_factory

        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        return "healthy"
    except Exception as exc:
        logger.warning("Database health check failed: %s", exc)
        return "unhealthy"


async def _check_redis() -> str:
    try:
        from app.db.redis import get_redis_manager

        mgr = get_redis_manager()
        if mgr is None:
            return "not_configured"
        await mgr.pool.ping()
        return "healthy"
    except Exception as exc:
        logger.warning("Redis health check failed: %s", exc)
        return "unhealthy"


async def _check_docker() -> str:
    try:
        import docker

        client = docker.from_env()
        client.ping()
        client.close()
        return "healthy"
    except Exception:
        return "unavailable"


@router.get("/health")
async def health_check() -> dict:
    db_status = await _check_database()
    redis_status = await _check_redis()
    docker_status = await _check_docker()

    overall = "healthy"
    if db_status != "healthy":
        overall = "degraded"
    if db_status == "unhealthy" and redis_status == "unhealthy":
        overall = "unhealthy"

    return {
        "status": overall,
        "database": db_status,
        "redis": redis_status,
        "docker": docker_status,
    }
