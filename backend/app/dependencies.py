from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Depends

from app.config import Settings, get_settings


def get_settings_dep() -> Settings:
    return get_settings()


async def get_db() -> AsyncGenerator:
    try:
        from app.db.session import async_session_factory

        async with async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    except ImportError:
        yield None


async def get_redis():
    try:
        from app.db.redis import get_redis_manager

        return get_redis_manager()
    except ImportError:
        return None


async def get_task_service(session=Depends(get_db)):
    from app.services.task_service import TaskService

    return TaskService(session)


async def get_settings_service(session=Depends(get_db)):
    from app.services.settings_service import SettingsService

    return SettingsService(session)


async def get_benchmark_service(session=Depends(get_db)):
    from app.services.benchmark_service import BenchmarkService

    return BenchmarkService(session)


async def get_sandbox_executor():
    from app.config import get_settings
    from app.sandbox.executor import CodeExecutor

    settings = get_settings()
    return CodeExecutor(settings)
