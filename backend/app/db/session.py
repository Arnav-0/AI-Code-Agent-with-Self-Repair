from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings


def _create_engine():
    settings = get_settings()
    echo = settings.log_level.upper() == "DEBUG"
    url = settings.database_url
    # SQLite doesn't support pool_size/max_overflow
    if url.startswith("sqlite"):
        return create_async_engine(url, echo=echo)
    return create_async_engine(
        url,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
        echo=echo,
    )


engine = _create_engine()

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
