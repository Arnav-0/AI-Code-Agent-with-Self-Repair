"""WebSocket endpoint for real-time agent streaming."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.agents.base import AgentOutput, AgentType
from app.models.schemas import (
    WSAgentCompleted,
    WSAgentStarted,
    WSEvent,
    WSExecutionCompleted,
    WSExecutionStarted,
    WSRepairFixApplied,
    WSRepairStarted,
    WSTaskCompleted,
    WSTaskFailed,
)

logger = logging.getLogger("codeforge.websocket")

router = APIRouter(tags=["WebSocket"])


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


class ConnectionManager:
    """Manages WebSocket connections per task."""

    def __init__(self) -> None:
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, task_id: str) -> None:
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = []
        self.active_connections[task_id].append(websocket)
        logger.info("WS connected for task %s", task_id)

    async def disconnect(self, websocket: WebSocket, task_id: str) -> None:
        if task_id in self.active_connections:
            try:
                self.active_connections[task_id].remove(websocket)
            except ValueError:
                pass
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
        logger.info("WS disconnected for task %s", task_id)

    async def broadcast_to_task(self, task_id: str, event: WSEvent) -> None:
        """Send event to all connections watching a task."""
        if task_id not in self.active_connections:
            return
        dead: list[WebSocket] = []
        for ws in list(self.active_connections[task_id]):
            try:
                await ws.send_json(event.model_dump(mode="json"))
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(ws, task_id)


manager = ConnectionManager()


class WebSocketAgentCallback:
    """Bridges agent events to WebSocket broadcasts."""

    def __init__(self, task_id: str, manager: ConnectionManager) -> None:
        self.task_id = task_id
        self.manager = manager

    async def _emit(self, event_type: str, data: dict) -> None:
        event = WSEvent(event=event_type, timestamp=_now(), data=data)
        await self.manager.broadcast_to_task(self.task_id, event)

    # ── AgentCallback protocol ────────────────────────────────────────────────

    def on_agent_start(self, agent_type: AgentType, input_data: dict) -> None:
        asyncio.create_task(
            self._emit(
                "agent.started",
                WSAgentStarted(
                    agent_type=agent_type.value,
                    step_order=0,
                    input_summary=str(input_data)[:200],
                ).model_dump(),
            )
        )

    def on_agent_thinking(self, agent_type: AgentType, chunk: str) -> None:
        asyncio.create_task(
            self._emit(
                "agent.thinking",
                {"agent_type": agent_type.value, "chunk": chunk},
            )
        )

    def on_agent_complete(self, agent_type: AgentType, output: AgentOutput) -> None:
        asyncio.create_task(
            self._emit(
                "agent.completed",
                WSAgentCompleted(
                    agent_type=agent_type.value,
                    output_summary=str(output.data)[:200],
                    tokens_used=output.tokens_used,
                    cost_usd=output.cost_usd,
                    duration_ms=output.duration_ms,
                ).model_dump(),
            )
        )

    def on_agent_error(self, agent_type: AgentType, error: str) -> None:
        asyncio.create_task(
            self._emit(
                "agent.error",
                {"agent_type": agent_type.value, "error": error},
            )
        )

    # ── Execution events ──────────────────────────────────────────────────────

    async def on_execution_started(
        self, task_id: str, container_id: Any, retry_number: int
    ) -> None:
        await self._emit(
            "execution.started",
            WSExecutionStarted(
                container_id=container_id, retry_number=retry_number
            ).model_dump(),
        )

    async def on_execution_stdout(self, task_id: str, line: str) -> None:
        await self._emit("execution.stdout", {"stream": "stdout", "line": line})

    async def on_execution_stderr(self, task_id: str, line: str) -> None:
        await self._emit("execution.stderr", {"stream": "stderr", "line": line})

    async def on_execution_completed(
        self,
        task_id: str,
        exit_code: int,
        execution_time_ms: int,
        memory_used_mb: Any,
    ) -> None:
        await self._emit(
            "execution.completed",
            WSExecutionCompleted(
                exit_code=exit_code,
                execution_time_ms=execution_time_ms,
                memory_used_mb=memory_used_mb,
            ).model_dump(),
        )

    # ── Repair events ─────────────────────────────────────────────────────────

    async def on_repair_started(
        self, task_id: str, retry_number: int, error_summary: str
    ) -> None:
        await self._emit(
            "repair.started",
            WSRepairStarted(
                retry_number=retry_number, error_summary=error_summary
            ).model_dump(),
        )

    async def on_repair_fix_applied(
        self, task_id: str, fixed_code: str, change_summary: str
    ) -> None:
        await self._emit(
            "repair.fix_applied",
            WSRepairFixApplied(
                fixed_code=fixed_code, change_summary=change_summary
            ).model_dump(),
        )

    # ── Task lifecycle ────────────────────────────────────────────────────────

    async def on_task_completed(
        self,
        task_id: str,
        final_code: str,
        final_output: str,
        total_cost: float,
        total_time_ms: int,
        retry_count: int,
    ) -> None:
        await self._emit(
            "task.completed",
            WSTaskCompleted(
                final_code=final_code,
                final_output=final_output,
                total_cost=total_cost,
                total_time_ms=total_time_ms,
                retry_count=retry_count,
            ).model_dump(),
        )

    async def on_task_failed(
        self, task_id: str, error_message: str, retry_count: int
    ) -> None:
        await self._emit(
            "task.failed",
            WSTaskFailed(
                error_message=error_message, retry_count=retry_count
            ).model_dump(),
        )

    async def on_status_change(self, task_id: str, new_status: str) -> None:
        await self._emit("task.status_changed", {"status": new_status})

    async def on_code_generated(
        self, task_id: str, code: str, language: str, subtask_index: int
    ) -> None:
        await self._emit(
            "code.generated",
            {"code": code, "language": language, "subtask_index": subtask_index},
        )

    # ── Research events ──────────────────────────────────────────────────────

    async def on_research_started(self, task_id: str) -> None:
        await self._emit("research.started", {"message": "Starting deep research..."})

    async def on_research_complete(self, task_id: str, findings: dict) -> None:
        await self._emit("research.complete", {"findings": findings})

    async def on_questions_ready(self, task_id: str, questions: list) -> None:
        await self._emit("questions.ready", {"questions": questions})

    async def on_answers_received(self, task_id: str, answers: dict) -> None:
        await self._emit("answers.received", {"answers": answers})


@router.websocket("/ws/tasks/{task_id}")
async def task_websocket(websocket: WebSocket, task_id: str) -> None:
    await manager.connect(websocket, task_id)
    try:
        while True:
            # Use timeout to send keepalive pings when client is silent
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(), timeout=15
                )
            except asyncio.TimeoutError:
                # Send a keepalive ping to prevent connection drop
                try:
                    await websocket.send_json(
                        {"event": "ping", "timestamp": _now().isoformat()}
                    )
                except Exception:
                    break
                continue

            if data.get("event") == "task.cancel":
                from app.api.tasks import _running_tasks

                bg_task = _running_tasks.get(task_id)
                if bg_task and not bg_task.done():
                    bg_task.cancel()
                    await websocket.send_json(
                        WSEvent(
                            event="task.cancelled",
                            timestamp=_now(),
                            data={"message": "Task cancellation requested"},
                        ).model_dump(mode="json")
                    )

            # Handle answer submissions for research Q&A
            if data.get("event") == "answers.submit":
                from app.api.tasks import _pending_answers
                answers = data.get("answers", {})
                future = _pending_answers.get(task_id)
                if future and not future.done():
                    future.set_result(answers)
                await websocket.send_json(
                    WSEvent(
                        event="answers.received",
                        timestamp=_now(),
                        data={"answers": answers},
                    ).model_dump(mode="json")
                )
    except WebSocketDisconnect:
        await manager.disconnect(websocket, task_id)
    except Exception as exc:
        logger.error("WebSocket error for task %s: %s", task_id, exc)
        await manager.disconnect(websocket, task_id)
