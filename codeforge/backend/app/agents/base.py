"""Abstract base agent class for all CodeForge agents."""

from __future__ import annotations

import json
import logging
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable


class AgentType(Enum):
    RESEARCHER = "researcher"
    QUESTIONER = "questioner"
    PLANNER = "planner"
    CODER = "coder"
    EXECUTOR = "executor"
    REVIEWER = "reviewer"


@dataclass
class AgentInput:
    data: dict
    task_id: str
    step_order: int


@dataclass
class AgentOutput:
    data: dict
    reasoning: str
    tokens_used: int
    cost_usd: float
    duration_ms: int
    success: bool
    error: str | None = None


@runtime_checkable
class AgentCallback(Protocol):
    def on_agent_start(self, agent_type: AgentType, input_data: dict) -> None: ...
    def on_agent_thinking(self, agent_type: AgentType, chunk: str) -> None: ...
    def on_agent_complete(self, agent_type: AgentType, output: AgentOutput) -> None: ...
    def on_agent_error(self, agent_type: AgentType, error: str) -> None: ...


class NullCallback:
    """No-op callback implementation."""

    def on_agent_start(self, agent_type: AgentType, input_data: dict) -> None:
        pass

    def on_agent_thinking(self, agent_type: AgentType, chunk: str) -> None:
        pass

    def on_agent_complete(self, agent_type: AgentType, output: "AgentOutput") -> None:
        pass

    def on_agent_error(self, agent_type: AgentType, error: str) -> None:
        pass

    async def on_status_change(self, task_id: str, new_status: str) -> None:
        pass

    async def on_code_generated(
        self, task_id: str, code: str, language: str, subtask_index: int
    ) -> None:
        pass

    async def on_execution_started(
        self, task_id: str, container_id: object, retry_number: int
    ) -> None:
        pass

    async def on_execution_completed(
        self,
        task_id: str,
        exit_code: int,
        execution_time_ms: int,
        memory_used_mb: object,
    ) -> None:
        pass

    async def on_repair_started(
        self, task_id: str, retry_number: int, error_summary: str
    ) -> None:
        pass

    async def on_repair_fix_applied(
        self, task_id: str, fixed_code: str, change_summary: str
    ) -> None:
        pass

    async def on_task_completed(
        self,
        task_id: str,
        final_code: str,
        final_output: str,
        total_cost: float,
        total_time_ms: int,
        retry_count: int,
    ) -> None:
        pass

    async def on_task_failed(
        self, task_id: str, error_message: str, retry_count: int
    ) -> None:
        pass

    async def on_research_started(self, task_id: str) -> None:
        pass

    async def on_research_complete(
        self, task_id: str, findings: dict
    ) -> None:
        pass

    async def on_questions_ready(
        self, task_id: str, questions: list
    ) -> None:
        pass

    async def on_answers_received(
        self, task_id: str, answers: dict
    ) -> None:
        pass


class BaseAgent(ABC):
    def __init__(
        self,
        llm: object,
        cost_tracker: object,
        callback: object | None = None,
    ) -> None:
        self.llm = llm
        self.cost_tracker = cost_tracker
        self.callback = callback or NullCallback()
        self._logger = self._get_logger()

    @property
    @abstractmethod
    def agent_type(self) -> AgentType: ...

    @abstractmethod
    async def _execute(self, input_data: AgentInput) -> AgentOutput: ...

    @abstractmethod
    def _build_system_prompt(self) -> str: ...

    @abstractmethod
    def _build_user_prompt(self, input_data: AgentInput) -> str: ...

    async def run(self, input_data: AgentInput) -> AgentOutput:
        """Template method — handles common concerns (logging, timing, error handling)."""
        self._logger.info("Starting %s agent for task %s", self.agent_type.value, input_data.task_id)
        self.callback.on_agent_start(self.agent_type, input_data.data)
        start = time.perf_counter()

        try:
            output = await self._execute(input_data)
            duration_ms = int((time.perf_counter() - start) * 1000)
            output.duration_ms = duration_ms
            self.callback.on_agent_complete(self.agent_type, output)
            self._logger.info(
                "%s agent completed in %dms (success=%s)",
                self.agent_type.value,
                duration_ms,
                output.success,
            )
            return output
        except Exception as exc:
            duration_ms = int((time.perf_counter() - start) * 1000)
            error_msg = str(exc)
            self._logger.error("%s agent error: %s", self.agent_type.value, error_msg)
            self.callback.on_agent_error(self.agent_type, error_msg)
            return AgentOutput(
                data={},
                reasoning="",
                tokens_used=0,
                cost_usd=0.0,
                duration_ms=duration_ms,
                success=False,
                error=error_msg,
            )

    async def _call_llm(self, user_prompt: str, system_prompt: str | None = None, structured: bool = True) -> object:
        """Call LLM, record cost, notify callback."""
        sp = system_prompt or self._build_system_prompt()
        if structured:
            response = await self.llm.generate_structured(user_prompt, sp)
        else:
            response = await self.llm.generate(user_prompt, sp)

        # Record cost with agent attribution
        if hasattr(self.cost_tracker, "record"):
            self.cost_tracker.record(response, agent_type=self.agent_type.value)

        content = getattr(response, "content", "")
        self.callback.on_agent_thinking(self.agent_type, content[:200])
        return response

    def _parse_json_response(self, text: str) -> dict:
        """Safely parse JSON from LLM response, handling markdown fences."""
        # Strip markdown fences
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON object or array using regex
        json_match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", cleaned)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        raise ValueError(
            f"Could not parse JSON from LLM response. "
            f"First 200 chars: {text[:200]!r}"
        )

    def _get_logger(self) -> logging.Logger:
        return logging.getLogger(f"codeforge.agent.{self.agent_type.value}")
