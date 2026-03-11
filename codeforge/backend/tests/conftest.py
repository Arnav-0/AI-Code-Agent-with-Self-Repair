from __future__ import annotations

from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.models.database import AgentTrace, Base, Task

# ─── Pytest markers ───────────────────────────────────────────────────────────


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "unit: unit tests")
    config.addinivalue_line("markers", "integration: requires Docker/DB")
    config.addinivalue_line("markers", "e2e: full stack tests")


# ─── Settings fixture ─────────────────────────────────────────────────────────


@pytest.fixture
def mock_settings() -> Settings:
    return Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        database_sync_url="sqlite:///:memory:",
        redis_url="redis://localhost:6379/0",
        openai_api_key="sk-test-key",
        anthropic_api_key="sk-ant-test-key",
        sandbox_image="codeforge-sandbox-python:latest",
        sandbox_timeout_seconds=10,
        sandbox_memory_limit_mb=256,
        log_level="DEBUG",
        log_format="text",
        secret_key="test-secret-key",
    )


# ─── Async DB session fixture ─────────────────────────────────────────────────


@pytest_asyncio.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


# ─── Mock LLM response fixture ────────────────────────────────────────────────


@pytest.fixture
def mock_llm_response():
    """Factory fixture returning canned LLM responses based on prompt keywords."""

    def _respond(prompt: str) -> str:
        prompt_lower = prompt.lower()
        if "plan" in prompt_lower or "planning" in prompt_lower:
            return '{"plan": [{"step": 1, "description": "Write code", "language": "python"}]}'
        elif "code" in prompt_lower or "coding" in prompt_lower or "implement" in prompt_lower:
            return '{"code": "def solution():\\n    return 42\\n", "language": "python"}'
        elif "review" in prompt_lower or "reviewing" in prompt_lower:
            return '{"passed": true, "feedback": "Code looks correct", "issues": []}'
        elif "repair" in prompt_lower or "fix" in prompt_lower:
            return '{"fixed_code": "def solution():\\n    return 42\\n", "changes": "Fixed syntax error"}'
        else:
            return '{"response": "OK"}'

    return _respond


# ─── Sample DB fixtures ───────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def sample_task(async_session: AsyncSession) -> Task:
    task = Task(
        prompt="Write a function that returns 42",
        status="pending",
    )
    async_session.add(task)
    await async_session.flush()
    await async_session.refresh(task)
    return task


@pytest_asyncio.fixture
async def sample_traces(
    async_session: AsyncSession, sample_task: Task
) -> list[AgentTrace]:
    traces = [
        AgentTrace(
            task_id=sample_task.id,
            agent_type="planner",
            input_data={"prompt": sample_task.prompt},
            output_data={"plan": [{"step": 1}]},
            tokens_used=100,
            step_order=1,
        ),
        AgentTrace(
            task_id=sample_task.id,
            agent_type="coder",
            input_data={"plan": [{"step": 1}]},
            output_data={"code": "def solution(): return 42"},
            tokens_used=200,
            step_order=2,
        ),
    ]
    for trace in traces:
        async_session.add(trace)
    await async_session.flush()
    return traces


# ─── Sandbox manager fixture ──────────────────────────────────────────────────


@pytest.fixture
def sandbox_manager():
    try:
        import docker  # type: ignore[import]
        client = docker.from_env()
        client.ping()
    except Exception:
        pytest.skip("Docker not available")

    from app.sandbox.manager import SandboxManager

    return SandboxManager(
        image="codeforge-sandbox-python:latest",
        timeout=10,
        memory_mb=256,
        cpu_limit=1.0,
        network_disabled=True,
    )
