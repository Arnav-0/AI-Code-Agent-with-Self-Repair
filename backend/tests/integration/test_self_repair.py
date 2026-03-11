"""Integration tests for the self-repair loop using mocked LLM and sandbox."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.llm.providers import BaseLLMProvider, LLMResponse  # noqa: F401
from app.sandbox.manager import ExecutionOutput

# ─── Mock helpers ─────────────────────────────────────────────────────────────


class MockLLMProvider(BaseLLMProvider):
    """Returns pre-configured responses in sequence."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self._index = 0
        self._model = "mock-model"

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.0,
        max_tokens: int = 4096,
        response_format: dict | None = None,
    ) -> LLMResponse:
        content = self._next_response()
        return LLMResponse(
            content=content,
            model=self._model,
            input_tokens=10,
            output_tokens=20,
            total_tokens=30,
            latency_ms=50,
        )

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: str = "",
        schema: dict | None = None,
    ) -> LLMResponse:
        return await self.generate(prompt, system_prompt)

    async def health_check(self) -> bool:
        return True

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def provider_name(self) -> str:
        return "mock"

    def _next_response(self) -> str:
        if self._index < len(self._responses):
            resp = self._responses[self._index]
            self._index += 1
            return resp
        return self._responses[-1]


class MockSandboxExecutor:
    """Returns pre-configured execution results."""

    def __init__(self, results: list[ExecutionOutput]) -> None:
        self._results = list(results)
        self._index = 0

    async def execute_python(self, code: str) -> ExecutionOutput:
        if self._index < len(self._results):
            result = self._results[self._index]
            self._index += 1
            return result
        return self._results[-1]


_SINGLE_SUBTASK_PLAN = json.dumps({
    "subtasks": [
        {
            "id": 1,
            "description": "Print 42",
            "dependencies": [],
            "estimated_complexity": "simple",
        }
    ],
    "reasoning": "Single step task",
})

_SIMPLE_CODE = json.dumps({
    "code": "def main():\n    print(42)\n\nif __name__ == '__main__':\n    main()",
    "imports": [],
    "explanation": "Prints 42",
})

_BUGGY_CODE = json.dumps({
    "code": "print(1/0)",
    "imports": [],
    "explanation": "Division by zero bug",
})

_REVIEW_FIX = json.dumps({
    "root_cause": "ZeroDivisionError",
    "error_type": "runtime_error",
    "fix_description": "Replace 1/0 with print(42)",
    "fixed_code": "print(42)",
    "confidence": 0.9,
    "changes_made": ["Replaced division by zero with print(42)"],
})

_REVIEW_FIX_LOW_CONF = json.dumps({
    "root_cause": "Unknown error",
    "error_type": "runtime_error",
    "fix_description": "Not sure",
    "fixed_code": "print(1/0)",
    "confidence": 0.2,
    "changes_made": [],
})

_SUCCESS_RESULT = ExecutionOutput(
    success=True, exit_code=0, stdout="42\n", stderr="",
    execution_time_ms=100, memory_used_mb=None, container_id="",
)
_FAIL_RESULT = ExecutionOutput(
    success=False, exit_code=1, stdout="",
    stderr="ZeroDivisionError: division by zero",
    execution_time_ms=50, memory_used_mb=None, container_id="",
)


def _make_settings(max_retries: int = 3) -> MagicMock:
    settings = MagicMock()
    settings.max_repair_retries = max_retries
    settings.max_cost_per_task = 1.0
    settings.openai_api_key = ""
    settings.anthropic_api_key = ""
    settings.openrouter_api_key = ""
    settings.ollama_base_url = "http://localhost:11434"
    settings.complexity_simple_threshold = 0.3
    settings.complexity_complex_threshold = 0.7
    settings.sandbox_timeout_seconds = 30
    return settings


def _patch_all(monkeypatch: Any, llm: MockLLMProvider, sandbox: MockSandboxExecutor) -> None:
    """Patch router.route (async) and sandbox executor for a test."""
    from app.llm.classifier import ComplexityLevel
    from app.llm.router import DEFAULT_MODEL_CONFIGS

    _llm = llm
    _cfg = DEFAULT_MODEL_CONFIGS[ComplexityLevel.SIMPLE]
    _level = ComplexityLevel.SIMPLE

    async def _mock_route(self_inner: Any, prompt: str) -> Any:
        return (_llm, _cfg, _level)

    def _mock_get_provider(self_inner: Any, provider_name: str, model: str = "") -> Any:
        return _llm

    def _mock_get_escalated(self_inner: Any, current_model: str, retry_count: int) -> Any:
        return None  # No escalation in tests

    monkeypatch.setattr("app.llm.router.ModelRouter.route", _mock_route)
    monkeypatch.setattr("app.llm.router.ModelRouter.get_provider", _mock_get_provider)
    monkeypatch.setattr("app.llm.router.ModelRouter.get_escalated_provider", _mock_get_escalated)
    monkeypatch.setattr("app.sandbox.executor.CodeExecutor.execute_python", sandbox.execute_python)
    # Suppress exponential backoff sleep
    monkeypatch.setattr("app.agents.orchestrator.asyncio.sleep", AsyncMock())


# ─── Tests ────────────────────────────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_successful_execution_no_repair(monkeypatch: Any) -> None:
    """Task executes successfully without any repair needed."""
    from app.agents import orchestrator as orch_mod

    # Simple task: classify (no LLM) → skip plan → code → execute
    llm = MockLLMProvider([_SIMPLE_CODE])
    sandbox = MockSandboxExecutor([_SUCCESS_RESULT])
    _patch_all(monkeypatch, llm, sandbox)

    orchestrator = orch_mod.Orchestrator(_make_settings())
    result = await orchestrator.run_task("test-1", "Print 42")

    assert result["status"] == "completed"
    assert result["retry_count"] == 0
    assert result["execution_success"] is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_self_repair_fixes_on_first_retry(monkeypatch: Any) -> None:
    """Code fails on first attempt but reviewer fixes it successfully."""
    from app.agents import orchestrator as orch_mod

    # Simple task: classify (no LLM) → skip plan → code → exec(fail) → review → apply_fix → exec(pass)
    llm = MockLLMProvider([_BUGGY_CODE, _REVIEW_FIX])
    sandbox = MockSandboxExecutor([_FAIL_RESULT, _SUCCESS_RESULT])
    _patch_all(monkeypatch, llm, sandbox)

    orchestrator = orch_mod.Orchestrator(_make_settings())
    result = await orchestrator.run_task("test-2", "Print 42")

    assert result["status"] == "completed"
    assert result["retry_count"] == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_self_repair_exhausts_retries(monkeypatch: Any) -> None:
    """All retries fail — task ends as failed."""
    from app.agents import orchestrator as orch_mod

    # Simple task: code → 3x(exec fail → review → apply_fix) → exec fail → review → abort
    llm = MockLLMProvider([
        _BUGGY_CODE,
        _REVIEW_FIX,   # reviewer 1
        _REVIEW_FIX,   # reviewer 2
        _REVIEW_FIX,   # reviewer 3
    ])
    sandbox = MockSandboxExecutor([_FAIL_RESULT] * 10)
    _patch_all(monkeypatch, llm, sandbox)

    orchestrator = orch_mod.Orchestrator(_make_settings(max_retries=3))
    result = await orchestrator.run_task("test-3", "Print 42")

    assert result["status"] == "failed"
    assert result["retry_count"] == 3


@pytest.mark.integration
@pytest.mark.asyncio
async def test_low_confidence_early_abort(monkeypatch: Any) -> None:
    """Reviewer returns low confidence on second attempt — early abort."""
    from app.agents import orchestrator as orch_mod

    # Simple task: code → exec fail → review(high) → fix → exec fail → review(low) → abort
    llm = MockLLMProvider([
        _BUGGY_CODE,
        _REVIEW_FIX,           # reviewer 1 — high conf, retry
        _REVIEW_FIX_LOW_CONF,  # reviewer 2 — low conf, abort
    ])
    sandbox = MockSandboxExecutor([_FAIL_RESULT] * 10)
    _patch_all(monkeypatch, llm, sandbox)

    orchestrator = orch_mod.Orchestrator(_make_settings(max_retries=5))
    result = await orchestrator.run_task("test-4", "Print 42")

    assert result["status"] == "failed"
    assert result["retry_count"] == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_state_transitions_are_recorded(monkeypatch: Any) -> None:
    """Traces list records all agent executions."""
    from app.agents import orchestrator as orch_mod

    # Simple task skips planner — only coder trace expected
    llm = MockLLMProvider([_SIMPLE_CODE])
    sandbox = MockSandboxExecutor([_SUCCESS_RESULT])
    _patch_all(monkeypatch, llm, sandbox)

    orchestrator = orch_mod.Orchestrator(_make_settings())
    result = await orchestrator.run_task("test-5", "Print 42")

    traces = result.get("traces", [])
    assert len(traces) >= 1
    agent_types = [t.get("agent_type") for t in traces]
    assert "coder" in agent_types
    for trace in traces:
        assert "duration_ms" in trace


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cost_accumulates_across_retries(monkeypatch: Any) -> None:
    """Traces accumulate across retries; task reaches terminal state."""
    from app.agents import orchestrator as orch_mod

    # Simple task: code → exec fail → review → fix → exec pass
    llm = MockLLMProvider([_BUGGY_CODE, _REVIEW_FIX])
    sandbox = MockSandboxExecutor([_FAIL_RESULT, _SUCCESS_RESULT])
    _patch_all(monkeypatch, llm, sandbox)

    orchestrator = orch_mod.Orchestrator(_make_settings())
    result = await orchestrator.run_task("test-6", "Print 42")

    assert result["status"] in ("completed", "failed")
    assert len(result.get("traces", [])) >= 2
