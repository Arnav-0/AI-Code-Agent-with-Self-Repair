from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import router
from app.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()

    # Setup structured logging
    try:
        from app.observability.logging import setup_logging
        setup_logging(level=settings.log_level, format=settings.log_format)
    except Exception:
        pass

    logger.info("Starting CodeForge backend...")

    # Auto-create database tables if they don't exist
    try:
        from app.db.session import engine
        from app.models.database import Base
        import app.models.conversation  # noqa: F401 — register conversation tables

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified/created")
    except Exception as e:
        logger.warning(f"Could not auto-create tables: {e}")

    # Setup OpenTelemetry tracing
    try:
        from app.observability.tracing import setup_tracing
        setup_tracing(
            service_name=settings.otel_service_name,
            otlp_endpoint=settings.otel_exporter_otlp_endpoint,
        )
    except Exception as e:
        logger.warning(f"OTel tracing not available: {e}")

    # Redis startup
    try:
        from app.db.redis import init_redis_manager

        redis_manager = init_redis_manager(settings.redis_url)
        await redis_manager.connect()
    except Exception as e:
        logger.warning(f"Redis not available: {e}")

    yield

    logger.info("Shutting down CodeForge backend...")
    try:
        from app.db.redis import get_redis_manager

        redis_manager = get_redis_manager()
        if redis_manager is not None:
            await redis_manager.disconnect()
    except Exception:
        pass


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="CodeForge",
        version="0.1.0",
        description="AI Code Agent with Self-Repair",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add correlation ID middleware
    try:
        from app.observability.logging import CorrelationIdMiddleware

        app.add_middleware(CorrelationIdMiddleware)
    except Exception:
        pass

    # Exception handlers
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "Not found"})

    @app.exception_handler(422)
    async def validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(500)
    async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Internal server error")
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    # Include all routes
    app.include_router(router, prefix="/api/v1")

    @app.get("/")
    async def root() -> dict:
        return {"name": "CodeForge", "version": "0.1.0", "status": "running"}

    return app


app = create_app()
