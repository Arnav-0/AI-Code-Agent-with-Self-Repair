"""End-to-end tests for the full CodeForge API pipeline using mock LLM/sandbox."""

from __future__ import annotations

import uuid
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from app.config import Settings
from app.models.database import Base

# ─── Fixtures ─────────────────────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        database_url=TEST_DATABASE_URL,
        database_sync_url="sqlite:///:memory:",
        redis_url="redis://localhost:6379/0",
        openai_api_key="sk-test",
        anthropic_api_key="sk-ant-test",
        sandbox_image="codeforge-sandbox-python:latest",
        sandbox_timeout_seconds=10,
        sandbox_memory_limit_mb=256,
        log_level="WARNING",
        log_format="text",
        secret_key="e2e-test-secret",
    )


@pytest_asyncio.fixture
async def test_client(test_settings) -> AsyncGenerator[AsyncClient, None]:
    """Create httpx AsyncClient wired to the FastAPI app with an in-memory SQLite DB.

    Each test gets its own engine + tables, so tests are fully isolated.
    Sessions are committed on each request so data persists within a test.
    """
    # StaticPool keeps a single connection for in-memory SQLite across all sessions
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    from app import dependencies
    from app.main import create_app

    app = create_app()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        # Use AsyncSession directly to avoid async_sessionmaker context manager
        # which triggers asyncio.shield — incompatible with Python 3.12 + pytest-asyncio
        session = AsyncSession(engine, expire_on_commit=False)
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    app.dependency_overrides[dependencies.get_db] = override_get_db

    with patch("app.db.redis.init_redis_manager", return_value=MagicMock(connect=AsyncMock())), \
         patch("app.db.redis.get_redis_manager", return_value=None), \
         patch("app.observability.tracing.setup_tracing", return_value=None):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield client

    await engine.dispose()


# ─── Tests ────────────────────────────────────────────────────────────────────

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_health_endpoint(test_client: AsyncClient) -> None:
    """GET /health returns 200."""
    response = await test_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_full_task_lifecycle(test_client: AsyncClient) -> None:
    """Create a task, verify 201, poll GET, check traces endpoint."""
    # Suppress background orchestrator (no real LLM)
    with patch("app.api.tasks.asyncio.create_task", side_effect=lambda coro: coro.close()):
        response = await test_client.post(
            "/api/v1/tasks/",
            json={"prompt": "Write a function that returns 42"},
        )
    assert response.status_code == 201, response.text
    data = response.json()
    assert "id" in data
    task_id = data["id"]
    assert data["status"] == "pending"
    assert data["prompt"] == "Write a function that returns 42"

    # GET the task
    response = await test_client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    task = response.json()
    assert task["id"] == task_id
    assert task["status"] == "pending"

    # GET traces (empty at this point — no agent ran)
    response = await test_client.get(f"/api/v1/tasks/{task_id}/traces")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_task_not_found(test_client: AsyncClient) -> None:
    """GET /tasks/{non_existent} returns 404."""
    fake_id = str(uuid.uuid4())
    response = await test_client.get(f"/api/v1/tasks/{fake_id}")
    assert response.status_code == 404


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_history_endpoint(test_client: AsyncClient) -> None:
    """Create multiple tasks and verify they appear in history with filtering."""
    prompts = [
        "Write hello world",
        "Compute fibonacci numbers",
        "Sort a list of integers",
    ]

    created_ids = []
    with patch("app.api.tasks.asyncio.create_task", side_effect=lambda coro: coro.close()):
        for prompt in prompts:
            resp = await test_client.post("/api/v1/tasks/", json={"prompt": prompt})
            assert resp.status_code == 201
            created_ids.append(resp.json()["id"])

    # GET /history/
    response = await test_client.get("/api/v1/history/")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= len(prompts)

    # Filter by status=pending
    response = await test_client.get("/api/v1/history/?status=pending")
    assert response.status_code == 200
    filtered = response.json()
    for item in filtered["items"]:
        assert item["status"] == "pending"

    # Search by keyword
    response = await test_client.get("/api/v1/history/?search=fibonacci")
    assert response.status_code == 200
    results = response.json()
    assert results["total"] >= 1
    assert any("fibonacci" in item["prompt"].lower() for item in results["items"])


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_settings_crud(test_client: AsyncClient) -> None:
    """GET settings returns defaults; PUT updates them; GET confirms update."""
    # GET defaults
    response = await test_client.get("/api/v1/settings/")
    assert response.status_code == 200
    settings = response.json()
    assert "llm" in settings
    assert "routing" in settings
    assert "sandbox" in settings
    assert "simple_threshold" in settings["routing"]
    assert "timeout_seconds" in settings["sandbox"]

    # PUT with updated routing thresholds
    update = {
        "routing": {
            "simple_threshold": 0.25,
            "complex_threshold": 0.75,
            "simple_model": "llama3:8b",
            "complex_model": "gpt-4",
        }
    }
    response = await test_client.put("/api/v1/settings/", json=update)
    assert response.status_code == 200
    updated = response.json()
    assert updated["routing"]["simple_threshold"] == 0.25
    assert updated["routing"]["complex_threshold"] == 0.75

    # GET confirms the update persisted to DB
    response = await test_client.get("/api/v1/settings/")
    assert response.status_code == 200
    confirmed = response.json()
    assert confirmed["routing"]["simple_threshold"] == 0.25


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_task_validation_rejects_empty_prompt(test_client: AsyncClient) -> None:
    """POST /tasks/ with empty prompt returns 422."""
    response = await test_client.post("/api/v1/tasks/", json={"prompt": ""})
    assert response.status_code in (400, 422)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_task_delete(test_client: AsyncClient) -> None:
    """Create a task, delete it, confirm 404 on second GET."""
    with patch("app.api.tasks.asyncio.create_task", side_effect=lambda coro: coro.close()):
        create_resp = await test_client.post(
            "/api/v1/tasks/", json={"prompt": "Task to be deleted"}
        )
    assert create_resp.status_code == 201
    task_id = create_resp.json()["id"]

    del_resp = await test_client.delete(f"/api/v1/tasks/{task_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

    get_resp = await test_client.get(f"/api/v1/tasks/{task_id}")
    assert get_resp.status_code == 404
