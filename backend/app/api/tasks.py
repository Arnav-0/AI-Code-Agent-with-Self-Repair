from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_task_service
from app.models.schemas import AgentTraceResponse, TaskCreate, TaskDetail, TaskResponse
from app.services.task_service import TaskService

logger = logging.getLogger("codeforge.api.tasks")

router = APIRouter(prefix="/tasks", tags=["Tasks"])

# Global registry of running orchestrator asyncio.Tasks keyed by task_id
_running_tasks: dict[str, asyncio.Task] = {}

# Pending answer futures for research Q&A flow
_pending_answers: dict[str, asyncio.Future] = {}


def _cleanup_task(task_id: str) -> None:
    """Remove a task from the registry when it completes."""
    _running_tasks.pop(task_id, None)


async def _update_task_status(task_id: str, status: str, db_session: Any) -> None:
    """Persist intermediate status changes to the database."""
    try:
        from sqlalchemy import select

        from app.models.database import Task as TaskModel

        async with db_session() as session:
            result = await session.execute(
                select(TaskModel).where(TaskModel.id == uuid.UUID(task_id))
            )
            task = result.scalar_one_or_none()
            if task and task.status not in ("completed", "failed", "cancelled"):
                task.status = status
                await session.commit()
    except Exception as exc:
        logger.debug("Status update for %s failed: %s", task_id, exc)


class _PersistentCallback:
    """Wraps WebSocketAgentCallback to also persist status to DB."""

    def __init__(self, ws_callback: Any, task_id: str, db_session: Any) -> None:
        self._ws = ws_callback
        self._task_id = task_id
        self._db_session = db_session

    def __getattr__(self, name: str) -> Any:
        return getattr(self._ws, name)

    async def on_status_change(self, task_id: str, new_status: str) -> None:
        await self._ws.on_status_change(task_id, new_status)
        await _update_task_status(self._task_id, new_status, self._db_session)


async def _save_task_result(task_id: str, result: dict, db_session: Any) -> None:
    """Save orchestrator result to DB, including agent traces and execution results."""
    try:
        from sqlalchemy import select

        from app.models.database import AgentTrace, ExecutionResult
        from app.models.database import Task as TaskModel

        tid = uuid.UUID(task_id)
        async with db_session() as session:
            task_result = await session.execute(
                select(TaskModel).where(TaskModel.id == tid)
            )
            task = task_result.scalar_one_or_none()
            if not task:
                return

            task.status = result.get("status", "completed")
            task.final_code = result.get("integrated_code", "")
            task.final_output = (result.get("execution_result") or {}).get("stdout", "")
            task.total_cost_usd = result.get("total_cost_usd", 0.0)
            task.total_time_ms = result.get("total_time_ms")
            task.retry_count = result.get("retry_count", 0)
            task.error_message = result.get("error_message")
            task.complexity = result.get("complexity")
            task.model_used = result.get("model_used")
            if result.get("plan"):
                task.plan = result["plan"]

            # Persist agent traces
            traces = result.get("traces", [])
            for i, trace_data in enumerate(traces):
                trace = AgentTrace(
                    task_id=tid,
                    agent_type=trace_data.get("agent_type", "unknown"),
                    input_data=trace_data.get("input_summary", {}),
                    output_data=trace_data.get("output_summary", {}),
                    reasoning=trace_data.get("reasoning", ""),
                    tokens_used=trace_data.get("tokens_used", 0),
                    cost_usd=trace_data.get("cost_usd", 0.0),
                    duration_ms=trace_data.get("duration_ms"),
                    step_order=i + 1,
                )
                session.add(trace)

            # Persist execution results (from error_history which tracks each attempt)
            error_history = result.get("error_history", [])
            exec_result = result.get("execution_result") or {}
            # Save the final execution result
            if exec_result and exec_result.get("exit_code") is not None:
                # Find the last coder/executor trace to attach this to
                # For now, create a standalone trace for execution
                exec_trace = AgentTrace(
                    task_id=tid,
                    agent_type="executor",
                    input_data={"code_length": len(result.get("integrated_code", ""))},
                    output_data={
                        "exit_code": exec_result.get("exit_code"),
                        "timed_out": exec_result.get("timed_out", False),
                    },
                    reasoning="Final execution" if result.get("status") == "completed" else "Failed execution",
                    tokens_used=0,
                    cost_usd=0.0,
                    duration_ms=exec_result.get("execution_time_ms"),
                    step_order=len(traces) + 1,
                )
                session.add(exec_trace)
                await session.flush()

                er = ExecutionResult(
                    trace_id=exec_trace.id,
                    exit_code=exec_result.get("exit_code", 1),
                    stdout=exec_result.get("stdout", "")[:50000],
                    stderr=exec_result.get("stderr", "")[:50000],
                    execution_time_ms=exec_result.get("execution_time_ms", 0),
                    memory_used_mb=exec_result.get("memory_used_mb"),
                    retry_number=result.get("retry_count", 0),
                )
                session.add(er)

            await session.commit()
    except Exception as db_exc:
        logger.error("Failed to update task %s in DB: %s", task_id, db_exc, exc_info=True)


async def _run_orchestrator(
    task_id: str, prompt: str, db_session: Any,
    context_code: str | None = None,
    research_enabled: bool = True,
) -> None:
    """Background task: research + classify + plan, then either await approval or execute."""
    try:
        from app.agents.orchestrator import Orchestrator
        from app.api.websocket import WebSocketAgentCallback, manager
        from app.config import get_settings

        # If there's context from a previous task, prepend it to the prompt
        effective_prompt = prompt
        if context_code:
            effective_prompt = (
                f"{prompt}\n\n"
                f"EXISTING CODE TO MODIFY/EXTEND:\n```python\n{context_code}\n```\n"
                f"Modify or extend the above code based on the instruction. "
                f"Return the COMPLETE updated code, not just the changes."
            )

        settings = get_settings()
        # Check if research is globally enabled in settings
        research_on = research_enabled and getattr(settings, "research_enabled", True)

        ws_callback = WebSocketAgentCallback(task_id=task_id, manager=manager)
        callback = _PersistentCallback(ws_callback, task_id, db_session)
        orchestrator = Orchestrator(settings=settings, callback=callback)

        # Phase 1: Classify + research + questions + optionally plan
        phase1 = await orchestrator.run_planning_only(
            task_id=task_id, prompt=effective_prompt, research_enabled=research_on,
        )

        # If research produced questions awaiting answers, wait for user response
        if phase1.get("status") == "awaiting_answers" and phase1.get("questions"):
            await _update_task_status(task_id, "awaiting_answers", db_session)

            # Save research findings to DB
            try:
                from sqlalchemy import select

                from app.models.database import Task as TaskModel

                async with db_session() as session:
                    task_result = await session.execute(
                        select(TaskModel).where(TaskModel.id == uuid.UUID(task_id))
                    )
                    task = task_result.scalar_one_or_none()
                    if task:
                        task.status = "awaiting_answers"
                        task.plan = {
                            "_research": phase1.get("research_findings", {}),
                            "_questions": phase1.get("questions", []),
                            "_meta": {
                                "complexity": phase1.get("complexity", ""),
                                "model_used": phase1.get("model_used", ""),
                                "cached_provider_name": phase1.get("cached_provider_name", ""),
                                "total_cost_usd": phase1.get("total_cost_usd", 0.0),
                                "total_tokens": phase1.get("total_tokens", 0),
                            },
                        }
                        await session.commit()
            except Exception as exc:
                logger.error("Failed to save research state for %s: %s", task_id, exc)

            # Wait for answers via WebSocket (with timeout)
            answer_future: asyncio.Future = asyncio.get_running_loop().create_future()
            _pending_answers[task_id] = answer_future
            try:
                answers = await asyncio.wait_for(answer_future, timeout=600)  # 10 min
            except asyncio.TimeoutError:
                logger.warning("Answer timeout for task %s — proceeding with defaults", task_id)
                # Use default answers from questions
                answers = {
                    str(q.get("id", i)): q.get("default_answer", "")
                    for i, q in enumerate(phase1.get("questions", []))
                }
            finally:
                _pending_answers.pop(task_id, None)

            # Inject answers into state and resume
            phase1["user_answers"] = answers
            phase1["status"] = "planning"

            # Now continue to plan+execute
            if phase1.get("complexity") == "hard":
                # Build an enriched state that carries research + answers into planning
                enriched_state = dict(phase1)
                enriched_state["research_enabled"] = False
                enriched_state["user_answers"] = answers
                enriched_state["status"] = "planning"

                plan_phase = await orchestrator.run_planning_only(
                    task_id=task_id, prompt=effective_prompt, research_enabled=False,
                )
                # Carry forward research data and answers into the plan phase
                plan_phase["research_findings"] = phase1.get("research_findings")
                plan_phase["user_answers"] = answers
                plan_phase["complexity"] = phase1.get("complexity", "hard")
                plan_phase["model_used"] = plan_phase.get("model_used") or phase1.get("model_used", "")
                plan_phase["cached_provider_name"] = plan_phase.get("cached_provider_name") or phase1.get("cached_provider_name", "")
                phase1 = plan_phase

                if phase1.get("plan"):
                    # Go to approval flow (existing logic below handles this)
                    pass
            else:
                # Simple/medium — go straight to execution
                phase1["research_enabled"] = False
                result = await orchestrator.run_from_plan(task_id=task_id, state=phase1)
                await _save_task_result(task_id, result, db_session)
                return

        # If hard task with a plan, pause for user approval
        if phase1.get("complexity") == "hard" and phase1.get("plan"):
            try:
                from sqlalchemy import select

                from app.models.database import Task as TaskModel

                async with db_session() as session:
                    task_result = await session.execute(
                        select(TaskModel).where(TaskModel.id == uuid.UUID(task_id))
                    )
                    task = task_result.scalar_one_or_none()
                    if task:
                        task.status = "awaiting_approval"
                        task.complexity = phase1.get("complexity")
                        task.model_used = phase1.get("model_used")
                        task.total_cost_usd = phase1.get("total_cost_usd", 0.0)
                        # Save plan + meta for resumption
                        task.plan = {
                            **(phase1.get("plan") or {}),
                            "_meta": {
                                "cached_provider_name": phase1.get("cached_provider_name", ""),
                                "total_cost_usd": phase1.get("total_cost_usd", 0.0),
                                "total_tokens": phase1.get("total_tokens", 0),
                            },
                        }
                        await session.commit()
            except Exception as exc:
                logger.error("Failed to save plan for %s: %s", task_id, exc)

            # Emit plan.ready event via WebSocket
            await callback.on_status_change(task_id, "awaiting_approval")
            if hasattr(ws_callback, "_emit"):
                plan_data = phase1.get("plan") or {}
                await ws_callback._emit("plan.ready", {
                    "plan": plan_data,
                    "complexity": phase1.get("complexity", ""),
                })
            logger.info("Task %s awaiting plan approval", task_id)
            return  # Stop here — user must approve

        # Simple/medium task — continue execution immediately using phase1 state
        result = await orchestrator.run_from_plan(task_id=task_id, state=phase1)
        await _save_task_result(task_id, result, db_session)

    except asyncio.CancelledError:
        logger.info("Task %s was cancelled", task_id)
        # Clean up any pending answer future
        pending = _pending_answers.pop(task_id, None)
        if pending and not pending.done():
            pending.cancel()
        # Mark task as cancelled in DB
        try:
            from sqlalchemy import select

            from app.db.session import async_session_factory
            from app.models.database import Task as TaskModel

            async with async_session_factory() as session:
                task_result = await session.execute(
                    select(TaskModel).where(TaskModel.id == uuid.UUID(task_id))
                )
                task = task_result.scalar_one_or_none()
                if task:
                    task.status = "cancelled"
                    task.error_message = "Task was cancelled by user"
                    await session.commit()
        except Exception:
            pass

        # Emit cancellation event via WebSocket
        try:
            from app.api.websocket import WSEvent, _now, manager

            event = WSEvent(
                event="task.cancelled",
                timestamp=_now(),
                data={"message": "Task was cancelled by user"},
            )
            await manager.broadcast_to_task(task_id, event)
        except Exception:
            pass
        raise

    except Exception as exc:
        logger.error("Orchestrator failed for task %s: %s", task_id, exc)
        # Try to mark task as failed
        try:
            from sqlalchemy import select

            from app.db.session import async_session_factory
            from app.models.database import Task as TaskModel

            async with async_session_factory() as session:
                task_result = await session.execute(
                    select(TaskModel).where(TaskModel.id == uuid.UUID(task_id))
                )
                task = task_result.scalar_one_or_none()
                if task:
                    task.status = "failed"
                    task.error_message = str(exc)
                    await session.commit()
        except Exception:
            pass


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    body: TaskCreate,
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    task = await service.create_task(body.prompt)
    task_id = str(task.id)

    # Start orchestrator as background task and track it
    try:
        from app.db.session import async_session_factory
        bg_task = asyncio.create_task(
            _run_orchestrator(
                task_id, body.prompt, async_session_factory,
                context_code=body.context_code,
                research_enabled=body.research_enabled,
            )
        )
        _running_tasks[task_id] = bg_task
        bg_task.add_done_callback(lambda _: _cleanup_task(task_id))
    except Exception as exc:
        logger.warning("Could not start orchestrator background task: %s", exc)

    return TaskResponse.model_validate(task)


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: uuid.UUID,
    service: TaskService = Depends(get_task_service),
) -> dict:
    task = await service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    tid = str(task_id)
    bg_task = _running_tasks.get(tid)
    if bg_task and not bg_task.done():
        bg_task.cancel()
        # Give it a moment to process the cancellation
        try:
            await asyncio.wait_for(asyncio.shield(bg_task), timeout=2.0)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass
        return {"success": True, "status": "cancelled"}

    # Task not running — check if it's already in a terminal state
    if task.status in ("completed", "failed", "cancelled"):
        return {"success": False, "status": task.status}

    # Task not tracked but still pending — update DB directly
    from sqlalchemy import select

    from app.db.session import async_session_factory
    from app.models.database import Task as TaskModel

    try:
        async with async_session_factory() as session:
            result = await session.execute(
                select(TaskModel).where(TaskModel.id == task_id)
            )
            db_task = result.scalar_one_or_none()
            if db_task and db_task.status not in ("completed", "failed", "cancelled"):
                db_task.status = "cancelled"
                db_task.error_message = "Task was cancelled by user"
                await session.commit()
                return {"success": True, "status": "cancelled"}
    except Exception:
        pass

    return {"success": False, "status": task.status}


@router.get("/{task_id}", response_model=TaskDetail)
async def get_task(
    task_id: uuid.UUID,
    service: TaskService = Depends(get_task_service),
) -> TaskDetail:
    task = await service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskDetail.model_validate(task)


@router.get("/{task_id}/traces", response_model=list[AgentTraceResponse])
async def get_task_traces(
    task_id: uuid.UUID,
    service: TaskService = Depends(get_task_service),
) -> list[AgentTraceResponse]:
    traces = await service.get_task_traces(task_id)
    return [AgentTraceResponse.model_validate(t) for t in traces]


@router.post("/{task_id}/answers")
async def submit_answers(
    task_id: uuid.UUID,
    body: dict,
    service: TaskService = Depends(get_task_service),
) -> dict:
    """Submit answers to research questions for a task awaiting answers."""
    task = await service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != "awaiting_answers":
        raise HTTPException(
            status_code=400,
            detail=f"Task is not awaiting answers (status: {task.status})",
        )

    tid = str(task_id)
    raw_answers = body.get("answers")
    if not isinstance(raw_answers, dict):
        raise HTTPException(status_code=422, detail="'answers' must be a dict mapping question id to answer string")
    # Sanitize: ensure all values are strings, truncate excessively long answers
    answers = {str(k): str(v)[:5000] for k, v in raw_answers.items()}

    # Resolve the pending future if it exists
    future = _pending_answers.get(tid)
    if future and not future.done():
        future.set_result(answers)
        return {"success": True, "status": "answers_received"}

    return {"success": False, "status": "no_pending_question_session"}


@router.post("/{task_id}/approve")
async def approve_task(
    task_id: uuid.UUID,
    service: TaskService = Depends(get_task_service),
) -> dict:
    """Approve a plan for a hard task, resuming execution."""
    task = await service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != "awaiting_approval":
        raise HTTPException(
            status_code=400,
            detail=f"Task is not awaiting approval (status: {task.status})",
        )

    tid = str(task_id)

    # Start the execution phase as a background task
    try:
        from app.db.session import async_session_factory

        bg_task = asyncio.create_task(
            _run_execution_phase(tid, task, async_session_factory)
        )
        _running_tasks[tid] = bg_task
        bg_task.add_done_callback(lambda _: _cleanup_task(tid))
    except Exception as exc:
        logger.warning("Could not start execution phase: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to start execution") from exc

    return {"success": True, "status": "executing"}


async def _run_execution_phase(task_id: str, task: Any, db_session: Any) -> None:
    """Resume execution for an approved task using its saved plan."""
    try:
        from app.agents.orchestrator import Orchestrator
        from app.api.websocket import WebSocketAgentCallback, manager
        from app.config import get_settings

        settings = get_settings()
        ws_callback = WebSocketAgentCallback(task_id=task_id, manager=manager)
        callback = _PersistentCallback(ws_callback, task_id, db_session)
        orchestrator = Orchestrator(settings=settings, callback=callback)

        # Reconstruct the state from saved plan
        plan_data = dict(task.plan) if task.plan else {}
        meta = plan_data.pop("_meta", {})

        state = orchestrator._initial_state(task_id, task.prompt)
        state["complexity"] = task.complexity or "hard"
        state["model_used"] = task.model_used or ""
        state["cached_provider_name"] = meta.get("cached_provider_name", "")
        state["total_cost_usd"] = meta.get("total_cost_usd", 0.0)
        state["total_tokens"] = meta.get("total_tokens", 0)
        state["plan"] = plan_data

        # Update DB status to executing
        await _update_task_status(task_id, "coding", db_session)
        await callback.on_status_change(task_id, "coding")

        result = await orchestrator.run_from_plan(task_id=task_id, state=state)
        await _save_task_result(task_id, result, db_session)

    except asyncio.CancelledError:
        logger.info("Execution phase for task %s was cancelled", task_id)
        try:
            from sqlalchemy import select

            from app.models.database import Task as TaskModel

            async with db_session() as session:
                task_result = await session.execute(
                    select(TaskModel).where(TaskModel.id == uuid.UUID(task_id))
                )
                db_task = task_result.scalar_one_or_none()
                if db_task:
                    db_task.status = "cancelled"
                    db_task.error_message = "Task was cancelled by user"
                    await session.commit()
        except Exception:
            pass
        raise

    except Exception as exc:
        logger.error("Execution phase failed for task %s: %s", task_id, exc, exc_info=True)
        try:
            from sqlalchemy import select

            from app.models.database import Task as TaskModel

            async with db_session() as session:
                task_result = await session.execute(
                    select(TaskModel).where(TaskModel.id == uuid.UUID(task_id))
                )
                db_task = task_result.scalar_one_or_none()
                if db_task:
                    db_task.status = "failed"
                    db_task.error_message = str(exc)
                    await session.commit()
        except Exception:
            pass


@router.delete("/{task_id}")
async def delete_task(
    task_id: uuid.UUID,
    service: TaskService = Depends(get_task_service),
) -> dict:
    # Cancel running task first if any
    tid = str(task_id)
    bg_task = _running_tasks.pop(tid, None)
    if bg_task and not bg_task.done():
        bg_task.cancel()

    deleted = await service.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True}
