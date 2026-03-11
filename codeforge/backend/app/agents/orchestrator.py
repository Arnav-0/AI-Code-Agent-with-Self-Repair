"""LangGraph state machine orchestrator for the full agent pipeline."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Optional

from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

logger = logging.getLogger("codeforge.orchestrator")


def _classify_error(stderr: str, exit_code: int, timed_out: bool) -> str:
    """Classify execution error into a structured category."""
    if timed_out:
        return "timeout"
    if not stderr:
        return "unknown" if exit_code != 0 else "success"
    lower = stderr.lower()
    if "syntaxerror" in lower or "indentationerror" in lower:
        return "syntax_error"
    if "modulenotfounderror" in lower or "importerror" in lower:
        return "import_error"
    if "memoryerror" in lower or "killed" in lower:
        return "memory_error"
    if "typeerror" in lower:
        return "type_error"
    if "keyerror" in lower or "indexerror" in lower or "attributeerror" in lower:
        return "access_error"
    if "valueerror" in lower:
        return "value_error"
    if "filenotfounderror" in lower or "permissionerror" in lower:
        return "io_error"
    if "recursionerror" in lower:
        return "recursion_error"
    if "connectionerror" in lower or "urlerror" in lower or "dns" in lower:
        return "network_error"
    if "zerodivisionerror" in lower:
        return "math_error"
    return "runtime_error"


class AgentState(TypedDict):
    # Input
    prompt: str
    task_id: str

    # Research
    research_findings: Optional[dict]
    research_queries: list
    questions: list
    user_answers: Optional[dict]
    research_enabled: bool

    # Classification
    complexity: str
    model_used: str

    # Planning
    plan: Optional[dict]
    current_subtask_index: int

    # Coding
    code_segments: dict
    integrated_code: str

    # Execution
    execution_result: Optional[dict]
    execution_success: bool

    # Review / Repair
    review_result: Optional[dict]
    retry_count: int
    max_retries: int
    attempted_fixes: list  # Track what fixes were tried
    escalated_model: str   # Current escalated model name (empty = use default)
    error_history: list    # [{error_class, error_message, fix_attempted, fix_worked}]

    # Cached routing
    cached_provider_name: str

    # Metadata
    total_cost_usd: float
    total_time_ms: int
    total_tokens: int
    traces: list
    error_message: Optional[str]
    status: str


def check_execution(state: AgentState) -> str:
    return "success" if state["execution_success"] else "failure"


def should_retry(state: AgentState) -> str:
    if state["retry_count"] >= state["max_retries"]:
        return "abort"
    review = state.get("review_result") or {}
    if review.get("confidence", 1.0) < 0.3 and state["retry_count"] >= 2:
        return "abort"
    return "retry"


def _create_node_functions(settings: Any, callback: Any = None) -> tuple:
    """Create node functions with injected dependencies (factory pattern)."""
    from app.llm.cost_tracker import CostTracker
    from app.llm.router import ModelRouter

    model_router = ModelRouter(settings)
    max_budget = getattr(settings, "max_cost_per_task", 1.0)
    cost_tracker = CostTracker(max_cost_per_task=max_budget)

    async def _get_provider(state):
        """Get the LLM provider, reusing classification result."""
        # Budget check before any LLM call
        if not cost_tracker.check_budget():
            raise RuntimeError(
                f"Budget exceeded: ${cost_tracker.total_cost:.4f} >= "
                f"${cost_tracker.max_cost_per_task:.4f} limit"
            )
        # If model was escalated during review, use the escalated model
        escalated = state.get("escalated_model", "")
        if escalated:
            try:
                provider_name = escalated.split("/")[0] if "/" in escalated else "openrouter"
                return model_router.get_provider(provider_name, escalated)
            except Exception:
                pass
        cached = state.get("cached_provider_name", "")
        if cached:
            try:
                return model_router.get_provider(cached, state.get("model_used", ""))
            except Exception:
                pass
        # Fallback to full route
        provider, _config, _level = await model_router.route(state["prompt"])
        return provider

    async def classify_node(state: AgentState) -> dict:
        if callback and hasattr(callback, "on_status_change"):
            await _safe_call(callback.on_status_change, state["task_id"], "classifying")
        try:
            provider, config, level = await model_router.route(state["prompt"])
            return {
                "complexity": level.value,
                "model_used": config.model,
                "cached_provider_name": config.provider,
                "status": "classifying",
            }
        except Exception as exc:
            logger.warning("Classification failed: %s — defaulting to ollama/llama3:8b", exc)
            return {"complexity": "medium", "model_used": "llama3:8b", "status": "classifying"}

    async def research_node(state: AgentState) -> dict:
        """Perform deep research on the task before planning/coding."""
        if not state.get("research_enabled", False):
            return {"research_findings": None, "questions": []}

        if callback and hasattr(callback, "on_status_change"):
            await _safe_call(callback.on_status_change, state["task_id"], "researching")
        if callback and hasattr(callback, "on_research_started"):
            await _safe_call(callback.on_research_started, state["task_id"])

        from app.agents.base import AgentInput
        from app.agents.researcher import ResearcherAgent
        from app.services.web_search import WebSearchService

        try:
            provider = await _get_provider(state)
        except Exception:
            from app.llm.providers import OllamaProvider
            provider = OllamaProvider(base_url=getattr(settings, "ollama_base_url", "http://localhost:11434"))

        # Create web search service
        web_search = WebSearchService(
            tavily_api_key=getattr(settings, "tavily_api_key", None),
            serp_api_key=getattr(settings, "serp_api_key", None),
        )

        agent = ResearcherAgent(provider, cost_tracker, callback, web_search=web_search)
        agent_input = AgentInput(
            data={"prompt": state["prompt"]},
            task_id=state["task_id"],
            step_order=1,
        )
        output = await agent.run(agent_input)

        try:
            await web_search.close()
        except Exception:
            pass

        traces = list(state.get("traces", []))
        traces.append({
            "agent_type": "researcher",
            "tokens_used": output.tokens_used,
            "cost_usd": output.cost_usd,
            "duration_ms": output.duration_ms,
            "success": output.success,
            "reasoning": output.reasoning,
            "input_summary": {"prompt": state["prompt"][:200]},
            "output_summary": {
                "findings_count": len((output.data or {}).get("key_findings", [])),
                "libraries": [lib.get("name", "") for lib in (output.data or {}).get("libraries", [])],
                "complexity": (output.data or {}).get("estimated_complexity", ""),
            },
        })

        if callback and hasattr(callback, "on_research_complete"):
            await _safe_call(callback.on_research_complete, state["task_id"], output.data or {})

        # Even partial/failed research data is useful — pass it through
        findings = output.data if output.data else None
        return {
            "research_findings": findings,
            "status": "researching",
            "traces": traces,
            "total_cost_usd": state["total_cost_usd"] + output.cost_usd,
            "total_tokens": state["total_tokens"] + output.tokens_used,
        }

    async def question_node(state: AgentState) -> dict:
        """Generate targeted questions based on research findings."""
        research = state.get("research_findings")
        if not research:
            return {"questions": [], "status": "questioning"}

        if callback and hasattr(callback, "on_status_change"):
            await _safe_call(callback.on_status_change, state["task_id"], "questioning")

        from app.agents.base import AgentInput
        from app.agents.questioner import QuestionerAgent

        try:
            provider = await _get_provider(state)
        except Exception:
            from app.llm.providers import OllamaProvider
            provider = OllamaProvider(base_url=getattr(settings, "ollama_base_url", "http://localhost:11434"))

        agent = QuestionerAgent(provider, cost_tracker, callback)
        agent_input = AgentInput(
            data={
                "prompt": state["prompt"],
                "research": research,
            },
            task_id=state["task_id"],
            step_order=len(state.get("traces", [])) + 1,
        )
        output = await agent.run(agent_input)

        traces = list(state.get("traces", []))
        traces.append({
            "agent_type": "questioner",
            "tokens_used": output.tokens_used,
            "cost_usd": output.cost_usd,
            "duration_ms": output.duration_ms,
            "success": output.success,
            "reasoning": output.reasoning,
            "input_summary": {"research_topics": len(research.get("key_findings", []))},
            "output_summary": {
                "question_count": len((output.data or {}).get("questions", [])),
                "confidence": (output.data or {}).get("confidence_without_answers", 0),
            },
        })

        questions = (output.data or {}).get("questions", [])
        ready = (output.data or {}).get("ready_to_proceed", False)
        confidence = (output.data or {}).get("confidence_without_answers", 1.0)

        # If high confidence or no questions, skip Q&A
        if ready or not questions or confidence >= 0.9:
            return {
                "questions": [],
                "status": "questioning",
                "traces": traces,
                "total_cost_usd": state["total_cost_usd"] + output.cost_usd,
                "total_tokens": state["total_tokens"] + output.tokens_used,
            }

        if callback and hasattr(callback, "on_questions_ready"):
            await _safe_call(callback.on_questions_ready, state["task_id"], questions)

        return {
            "questions": questions,
            "status": "awaiting_answers",
            "traces": traces,
            "total_cost_usd": state["total_cost_usd"] + output.cost_usd,
            "total_tokens": state["total_tokens"] + output.tokens_used,
        }

    async def plan_node(state: AgentState) -> dict:
        if callback and hasattr(callback, "on_status_change"):
            await _safe_call(callback.on_status_change, state["task_id"], "planning")
        from app.agents.base import AgentInput
        from app.agents.planner import PlannerAgent

        try:
            provider = await _get_provider(state)
        except Exception:
            from app.llm.providers import OllamaProvider
            provider = OllamaProvider(base_url=getattr(settings, "ollama_base_url", "http://localhost:11434"))

        agent = PlannerAgent(provider, cost_tracker, callback)

        # Enrich prompt with research context and user answers
        enriched_prompt = state["prompt"]
        research = state.get("research_findings")
        if research:
            ctx_parts = [enriched_prompt, "\n\n--- RESEARCH CONTEXT ---"]
            if research.get("recommended_approach"):
                ctx_parts.append(f"Approach: {research['recommended_approach']}")
            if research.get("libraries"):
                libs = ", ".join(lib.get("name", "") for lib in research["libraries"])
                ctx_parts.append(f"Libraries: {libs}")
            if research.get("architecture_notes"):
                ctx_parts.append(f"Architecture: {research['architecture_notes']}")
            if research.get("risks"):
                ctx_parts.append(f"Risks: {', '.join(research['risks'])}")
            enriched_prompt = "\n".join(ctx_parts)

        answers = state.get("user_answers")
        if answers:
            answer_lines = ["\n\n--- USER CLARIFICATIONS ---"]
            for qid, ans in answers.items():
                answer_lines.append(f"Q{qid}: {ans}")
            enriched_prompt += "\n".join(answer_lines)

        agent_input = AgentInput(
            data={"prompt": enriched_prompt},
            task_id=state["task_id"],
            step_order=len(state.get("traces", [])) + 1,
        )
        output = await agent.run(agent_input)

        traces = list(state.get("traces", []))
        traces.append({
            "agent_type": "planner",
            "tokens_used": output.tokens_used,
            "cost_usd": output.cost_usd,
            "duration_ms": output.duration_ms,
            "success": output.success,
            "reasoning": output.reasoning,
            "input_summary": {"prompt": state["prompt"][:200]},
            "output_summary": {"subtask_count": len((output.data or {}).get("subtasks", []))},
        })

        return {
            "plan": output.data if output.success else None,
            "status": "planning",
            "traces": traces,
            "total_cost_usd": state["total_cost_usd"] + output.cost_usd,
            "total_tokens": state["total_tokens"] + output.tokens_used,
        }

    async def code_node(state: AgentState) -> dict:
        # Budget check before LLM call
        if hasattr(cost_tracker, 'check_budget') and not cost_tracker.check_budget():
            return {"status": "failed", "error_message": "Budget exceeded ($%.4f)" % cost_tracker.total_cost}

        if callback and hasattr(callback, "on_status_change"):
            await _safe_call(callback.on_status_change, state["task_id"], "coding")
        from app.agents.base import AgentInput
        from app.agents.coder import CoderAgent

        plan = state.get("plan") or {}
        subtasks = plan.get("subtasks", [])

        if not subtasks:
            logger.warning("No subtasks in plan — generating code directly from prompt")
            # Synthesise a single subtask from the prompt so the coder has
            # something to work with instead of producing empty code.
            # Enrich description with research context when available
            description = state["prompt"]
            research = state.get("research_findings")
            if research:
                ctx = []
                if research.get("recommended_approach"):
                    ctx.append(f"Approach: {research['recommended_approach']}")
                if research.get("libraries"):
                    libs = ", ".join(lib.get("name", "") for lib in research["libraries"])
                    ctx.append(f"Libraries: {libs}")
                if research.get("architecture_notes"):
                    ctx.append(f"Architecture: {research['architecture_notes']}")
                if ctx:
                    description += "\n\n--- RESEARCH CONTEXT ---\n" + "\n".join(ctx)
            answers = state.get("user_answers")
            if answers:
                answer_lines = ["\n--- USER CLARIFICATIONS ---"]
                for qid, ans in answers.items():
                    answer_lines.append(f"Q{qid}: {ans}")
                description += "\n".join(answer_lines)
            subtasks = [{
                "id": 1,
                "description": description,
                "dependencies": [],
                "estimated_complexity": state.get("complexity", "medium"),
            }]

        try:
            provider = await _get_provider(state)
        except Exception:
            from app.llm.providers import OllamaProvider
            provider = OllamaProvider(base_url=getattr(settings, "ollama_base_url", "http://localhost:11434"))

        agent = CoderAgent(provider, cost_tracker, callback)

        # Group subtasks by dependency level for parallel execution
        dep_levels: dict[int, list] = {}
        for subtask in subtasks:
            deps = subtask.get("dependencies", [])
            level = 0
            for dep_id in deps:
                # Find the dep's level
                for lvl, tasks_at_lvl in dep_levels.items():
                    if any(t["id"] == dep_id for t in tasks_at_lvl):
                        level = max(level, lvl + 1)
            dep_levels.setdefault(level, []).append(subtask)

        code_segments: dict[int, str] = {}
        total_cost = state["total_cost_usd"]
        total_tokens = state["total_tokens"]
        traces = list(state.get("traces", []))

        for level_num in sorted(dep_levels.keys()):
            level_tasks = dep_levels[level_num]

            async def run_subtask(subtask):
                agent_input = AgentInput(
                    data={
                        "subtask": subtask,
                        "plan": plan,
                        "prior_code": dict(code_segments),
                    },
                    task_id=state["task_id"],
                    step_order=len(traces) + 1,
                )
                return subtask["id"], await agent.run(agent_input)

            # Run independent subtasks in parallel
            results = await asyncio.gather(
                *[run_subtask(st) for st in level_tasks],
                return_exceptions=True,
            )

            for result in results:
                if isinstance(result, Exception):
                    logger.error("Subtask failed: %s", result)
                    continue
                sid, output = result
                if output.success:
                    code_segments[sid] = output.data.get("code", "")
                    if callback and hasattr(callback, "on_code_generated"):
                        await _safe_call(
                            callback.on_code_generated,
                            state["task_id"],
                            output.data.get("code", ""),
                            "python",
                            sid,
                        )
                total_cost += output.cost_usd
                total_tokens += output.tokens_used
                traces.append({
                    "agent_type": "coder",
                    "tokens_used": output.tokens_used,
                    "cost_usd": output.cost_usd,
                    "duration_ms": output.duration_ms,
                    "success": output.success,
                    "reasoning": output.reasoning,
                    "input_summary": {"subtask_id": sid},
                    "output_summary": {"code_length": len(output.data.get("code", ""))},
                })

        # Integrate code segments — use proper merging for multi-subtask plans
        if len(code_segments) > 1:
            integration_code = code_segments.get(max(code_segments.keys()), "")
            integrated = CoderAgent._merge_code(code_segments, integration_code)
        elif code_segments:
            integrated = code_segments.get(max(code_segments.keys()), "")
        else:
            integrated = ""

        return {
            "code_segments": code_segments,
            "integrated_code": integrated,
            "status": "coding",
            "traces": traces,
            "total_cost_usd": total_cost,
            "total_tokens": total_tokens,
        }

    async def execute_node(state: AgentState) -> dict:
        if callback and hasattr(callback, "on_status_change"):
            await _safe_call(callback.on_status_change, state["task_id"], "executing")
        from app.sandbox.executor import CodeExecutor

        try:
            executor = CodeExecutor(settings)
            if callback and hasattr(callback, "on_execution_started"):
                await _safe_call(callback.on_execution_started, state["task_id"], None, state["retry_count"])

            result = await executor.execute_python(state["integrated_code"])

            # Stream stdout/stderr lines to WebSocket so frontend shows them
            if result.stdout and callback and hasattr(callback, "on_execution_stdout"):
                for line in result.stdout.splitlines():
                    await _safe_call(callback.on_execution_stdout, state["task_id"], line)
            if result.stderr and callback and hasattr(callback, "on_execution_stderr"):
                for line in result.stderr.splitlines():
                    await _safe_call(callback.on_execution_stderr, state["task_id"], line)

            if callback and hasattr(callback, "on_execution_completed"):
                await _safe_call(
                    callback.on_execution_completed,
                    state["task_id"],
                    result.exit_code,
                    result.execution_time_ms,
                    result.memory_used_mb,
                )

            # If this execution succeeds after a repair, mark the last fix as working
            error_history = list(state.get("error_history", []))
            if result.success and state["retry_count"] > 0 and error_history:
                error_history[-1]["fix_worked"] = True

            exec_data = {
                "execution_result": {
                    "exit_code": result.exit_code,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "execution_time_ms": result.execution_time_ms,
                    "memory_used_mb": result.memory_used_mb,
                    "timed_out": result.timed_out,
                },
                "execution_success": result.success,
                "status": "executing",
            }
            if error_history:
                exec_data["error_history"] = error_history
            return exec_data
        except Exception as exc:
            logger.error("Execution error: %s", exc)
            return {
                "execution_result": {
                    "exit_code": 1,
                    "stdout": "",
                    "stderr": str(exc),
                    "execution_time_ms": 0,
                    "memory_used_mb": None,
                    "timed_out": False,
                },
                "execution_success": False,
                "status": "executing",
            }

    async def review_node(state: AgentState) -> dict:
        # Budget check before LLM call
        if hasattr(cost_tracker, 'check_budget') and not cost_tracker.check_budget():
            return {
                "review_result": {"confidence": 0.0},
                "retry_count": state["max_retries"],  # Force abort
                "status": "failed",
                "error_message": "Budget exceeded ($%.4f)" % cost_tracker.total_cost,
            }

        if callback and hasattr(callback, "on_status_change"):
            await _safe_call(callback.on_status_change, state["task_id"], "reviewing")
        from app.agents.base import AgentInput
        from app.agents.reviewer import ReviewerAgent

        exec_result = state.get("execution_result") or {}
        error_summary = exec_result.get("stderr", "") or exec_result.get("stdout", "")

        if callback and hasattr(callback, "on_repair_started"):
            await _safe_call(
                callback.on_repair_started,
                state["task_id"],
                state["retry_count"] + 1,
                error_summary[:200],
            )

        # Try model escalation on retries — use a stronger model for repair
        escalated = None
        current_model = state.get("model_used", "")
        retry_count = state["retry_count"]
        if retry_count > 0 and current_model:
            escalated = model_router.get_escalated_provider(current_model, retry_count)

        if escalated:
            provider, escalated_model = escalated
            logger.info(
                "Review using escalated model %s (retry #%d)",
                escalated_model, retry_count + 1,
            )
        else:
            try:
                provider = await _get_provider(state)
            except Exception:
                from app.llm.providers import OllamaProvider
                provider = OllamaProvider(base_url=getattr(settings, "ollama_base_url", "http://localhost:11434"))

        agent = ReviewerAgent(provider, cost_tracker, callback)
        agent_input = AgentInput(
            data={
                "code": state["integrated_code"],
                "error": exec_result,
                "attempt": state["retry_count"] + 1,
                "max_attempts": state["max_retries"],
                "original_task": state["prompt"],
                "previous_fixes": state.get("attempted_fixes", []),
            },
            task_id=state["task_id"],
            step_order=len(state.get("traces", [])) + 1,
        )
        output = await agent.run(agent_input)

        traces = list(state.get("traces", []))
        traces.append({
            "agent_type": "reviewer",
            "tokens_used": output.tokens_used,
            "cost_usd": output.cost_usd,
            "duration_ms": output.duration_ms,
            "success": output.success,
            "reasoning": (output.data or {}).get("root_cause", ""),
            "input_summary": {"error_class": error_summary[:100]},
            "output_summary": {
                "confidence": (output.data or {}).get("confidence", 0),
                "error_type": (output.data or {}).get("error_type", ""),
            },
        })

        # Track error in history with structured classification
        error_history = list(state.get("error_history", []))
        error_type = _classify_error(
            exec_result.get("stderr", ""),
            exec_result.get("exit_code", 1),
            exec_result.get("timed_out", False),
        )
        error_history.append({
            "error_class": error_summary[:100] if error_summary else "",
            "error_type": error_type,
            "error_message": exec_result.get("stderr", "")[:300],
            "fix_attempted": (output.data or {}).get("fix_description", "") if output.success else "",
            "fix_worked": False,  # Updated by execute_node if next run succeeds
        })

        result = {
            "review_result": output.data if output.success else {"confidence": 0.0},
            "retry_count": state["retry_count"] + 1,
            "status": "reviewing",
            "traces": traces,
            "total_cost_usd": state["total_cost_usd"] + output.cost_usd,
            "total_tokens": state["total_tokens"] + output.tokens_used,
            "error_history": error_history,
        }

        # Store escalated model info if escalation occurred
        if escalated:
            result["escalated_model"] = escalated_model
            result["model_used"] = escalated_model

        return result

    async def apply_fix_node(state: AgentState) -> dict:
        if callback and hasattr(callback, "on_status_change"):
            await _safe_call(callback.on_status_change, state["task_id"], "repairing")
        review = state.get("review_result") or {}
        fixed_code = review.get("fixed_code", state["integrated_code"])
        change_summary = review.get("fix_description", "")

        if callback and hasattr(callback, "on_repair_fix_applied"):
            await _safe_call(
                callback.on_repair_fix_applied,
                state["task_id"],
                fixed_code,
                change_summary,
            )

        # Track attempted fix
        attempted_fixes = list(state.get("attempted_fixes", []))
        attempted_fixes.append({
            "attempt": state["retry_count"],
            "error_class": (state.get("execution_result") or {}).get("stderr", "")[:100],
            "fix_description": change_summary,
        })

        # Brief pause before re-execution (avoid hammering LLM on rapid retries)
        await asyncio.sleep(0.5)

        return {"integrated_code": fixed_code, "status": "repairing", "attempted_fixes": attempted_fixes}

    async def finalize_node(state: AgentState) -> dict:
        if callback and hasattr(callback, "on_status_change"):
            await _safe_call(callback.on_status_change, state["task_id"], "completed")
        exec_result = state.get("execution_result") or {}

        if callback and hasattr(callback, "on_task_completed"):
            await _safe_call(
                callback.on_task_completed,
                state["task_id"],
                state["integrated_code"],
                exec_result.get("stdout", ""),
                state["total_cost_usd"],
                0,
                state["retry_count"],
            )

        # Attach cost summary from tracker
        summary = cost_tracker.get_summary()
        logger.info(
            "Task %s cost: $%.4f (savings vs gpt-4o: $%.4f)",
            state["task_id"], summary["total_cost"], summary["estimated_savings"],
        )
        return {"status": "completed", "error_message": None, "total_cost_usd": summary["total_cost"]}

    async def fail_node(state: AgentState) -> dict:
        if callback and hasattr(callback, "on_status_change"):
            await _safe_call(callback.on_status_change, state["task_id"], "failed")
        exec_result = state.get("execution_result") or {}
        error = exec_result.get("stderr", "") or exec_result.get("stdout", "Error")

        if callback and hasattr(callback, "on_task_failed"):
            await _safe_call(
                callback.on_task_failed,
                state["task_id"],
                error,
                state["retry_count"],
            )

        return {"status": "failed", "error_message": error}

    return (
        classify_node,
        research_node,
        question_node,
        plan_node,
        code_node,
        execute_node,
        review_node,
        apply_fix_node,
        finalize_node,
        fail_node,
    )


async def _safe_call(fn: Any, *args: Any) -> None:
    """Safely call a callback function, ignoring errors."""
    try:
        result = fn(*args)
        if asyncio.iscoroutine(result):
            await result
    except Exception as exc:
        logger.debug("Callback error: %s", exc)


def build_agent_graph(settings: Any = None, callback: Any = None):
    """Build and compile the LangGraph state machine."""
    if settings is None:
        from app.config import get_settings
        settings = get_settings()

    (
        classify_node,
        research_node,
        question_node,
        plan_node,
        code_node,
        execute_node,
        review_node,
        apply_fix_node,
        finalize_node,
        fail_node,
    ) = _create_node_functions(settings, callback)

    graph = StateGraph(AgentState)

    graph.add_node("classify", classify_node)
    graph.add_node("research", research_node)
    graph.add_node("question", question_node)
    graph.add_node("plan", plan_node)
    graph.add_node("code", code_node)
    graph.add_node("execute", execute_node)
    graph.add_node("review", review_node)
    graph.add_node("apply_fix", apply_fix_node)
    graph.add_node("finalize", finalize_node)
    graph.add_node("fail", fail_node)

    def after_classify(state: AgentState) -> str:
        if state.get("research_enabled", False):
            return "research"
        return "plan" if state.get("complexity") == "hard" else "code"

    def after_question(state: AgentState) -> str:
        # If questions were generated and status is awaiting_answers, stop here
        if state.get("questions") and state.get("status") == "awaiting_answers":
            return "stop"
        return "plan" if state.get("complexity") == "hard" else "code"

    graph.set_entry_point("classify")
    graph.add_conditional_edges("classify", after_classify, {
        "research": "research",
        "plan": "plan",
        "code": "code",
    })
    graph.add_edge("research", "question")
    graph.add_conditional_edges("question", after_question, {
        "stop": END,
        "plan": "plan",
        "code": "code",
    })
    graph.add_edge("plan", "code")
    graph.add_edge("code", "execute")

    graph.add_conditional_edges("execute", check_execution, {
        "success": "finalize",
        "failure": "review",
    })
    graph.add_conditional_edges("review", should_retry, {
        "retry": "apply_fix",
        "abort": "fail",
    })

    graph.add_edge("apply_fix", "execute")
    graph.add_edge("finalize", END)
    graph.add_edge("fail", END)

    return graph.compile()


def build_planning_graph(settings: Any = None, callback: Any = None):
    """Build a graph that runs classify + research + questions + optional plan, then stops."""
    if settings is None:
        from app.config import get_settings
        settings = get_settings()

    nodes = _create_node_functions(settings, callback)
    classify_fn, research_fn, question_fn, plan_fn = nodes[0], nodes[1], nodes[2], nodes[3]

    graph = StateGraph(AgentState)
    graph.add_node("classify", classify_fn)
    graph.add_node("research", research_fn)
    graph.add_node("question", question_fn)
    graph.add_node("plan", plan_fn)

    def after_classify(state: AgentState) -> str:
        if state.get("research_enabled", False):
            return "research"
        return "plan" if state.get("complexity") == "hard" else "skip"

    def after_question(state: AgentState) -> str:
        if state.get("questions") and state.get("status") == "awaiting_answers":
            return "stop"
        return "plan" if state.get("complexity") == "hard" else "skip"

    graph.set_entry_point("classify")
    graph.add_conditional_edges("classify", after_classify, {
        "research": "research",
        "plan": "plan",
        "skip": END,
    })
    graph.add_edge("research", "question")
    graph.add_conditional_edges("question", after_question, {
        "stop": END,
        "plan": "plan",
        "skip": END,
    })
    graph.add_edge("plan", END)
    return graph.compile()


def build_execution_graph(settings: Any = None, callback: Any = None):
    """Build a graph for code → execute → review/repair loop (no classify/plan)."""
    if settings is None:
        from app.config import get_settings
        settings = get_settings()

    nodes = _create_node_functions(settings, callback)
    code_fn, execute_fn, review_fn, apply_fix_fn, finalize_fn, fail_fn = (
        nodes[4], nodes[5], nodes[6], nodes[7], nodes[8], nodes[9]
    )

    graph = StateGraph(AgentState)
    graph.add_node("code", code_fn)
    graph.add_node("execute", execute_fn)
    graph.add_node("review", review_fn)
    graph.add_node("apply_fix", apply_fix_fn)
    graph.add_node("finalize", finalize_fn)
    graph.add_node("fail", fail_fn)

    graph.set_entry_point("code")
    graph.add_edge("code", "execute")
    graph.add_conditional_edges("execute", check_execution, {
        "success": "finalize",
        "failure": "review",
    })
    graph.add_conditional_edges("review", should_retry, {
        "retry": "apply_fix",
        "abort": "fail",
    })
    graph.add_edge("apply_fix", "execute")
    graph.add_edge("finalize", END)
    graph.add_edge("fail", END)
    return graph.compile()


class Orchestrator:
    def __init__(self, settings: Any, callback: Any = None) -> None:
        self.settings = settings
        self.callback = callback
        self.graph = build_agent_graph(settings, callback)

    def _initial_state(self, task_id: str, prompt: str, research_enabled: bool = False) -> AgentState:
        max_retries = getattr(self.settings, "max_repair_retries", 3)
        return {
            "prompt": prompt,
            "task_id": task_id,
            "research_findings": None,
            "research_queries": [],
            "questions": [],
            "user_answers": None,
            "research_enabled": research_enabled,
            "complexity": "",
            "model_used": "",
            "cached_provider_name": "",
            "plan": None,
            "current_subtask_index": 0,
            "code_segments": {},
            "integrated_code": "",
            "execution_result": None,
            "execution_success": False,
            "review_result": None,
            "retry_count": 0,
            "max_retries": max_retries,
            "attempted_fixes": [],
            "escalated_model": "",
            "error_history": [],
            "total_cost_usd": 0.0,
            "total_time_ms": 0,
            "total_tokens": 0,
            "traces": [],
            "error_message": None,
            "status": "pending",
        }

    async def run_task(self, task_id: str, prompt: str, research_enabled: bool = False) -> AgentState:
        """Execute the full agent pipeline for a task."""
        initial_state = self._initial_state(task_id, prompt, research_enabled=research_enabled)
        logger.info("Starting orchestrator for task %s", task_id)
        start = time.perf_counter()
        result = await self.graph.ainvoke(initial_state)
        result["total_time_ms"] = int((time.perf_counter() - start) * 1000)
        logger.info("Task %s finished with status: %s in %dms", task_id, result.get("status"), result["total_time_ms"])
        return result

    async def run_planning_only(self, task_id: str, prompt: str, research_enabled: bool = False) -> AgentState:
        """Run classify + research + questions + optional plan. Returns intermediate state."""
        planning_graph = build_planning_graph(self.settings, self.callback)
        initial_state = self._initial_state(task_id, prompt, research_enabled=research_enabled)
        logger.info("Running planning phase for task %s", task_id)
        result = await planning_graph.ainvoke(initial_state)
        logger.info("Planning done for task %s: complexity=%s, has_plan=%s",
                     task_id, result.get("complexity"), bool(result.get("plan")))
        return result

    async def run_from_plan(self, task_id: str, state: AgentState) -> AgentState:
        """Execute from code node with a pre-built plan state."""
        execution_graph = build_execution_graph(self.settings, self.callback)
        logger.info("Resuming execution for task %s from plan", task_id)
        start = time.perf_counter()
        result = await execution_graph.ainvoke(state)
        result["total_time_ms"] = int((time.perf_counter() - start) * 1000)
        logger.info("Task %s finished with status: %s in %dms", task_id, result.get("status"), result["total_time_ms"])
        return result


# Module-level standalone node functions for testing
async def classify_node(state: AgentState) -> dict:
    from app.config import get_settings
    nodes = _create_node_functions(get_settings())
    return await nodes[0](state)


async def research_node(state: AgentState) -> dict:
    from app.config import get_settings
    nodes = _create_node_functions(get_settings())
    return await nodes[1](state)


async def question_node(state: AgentState) -> dict:
    from app.config import get_settings
    nodes = _create_node_functions(get_settings())
    return await nodes[2](state)


async def plan_node(state: AgentState) -> dict:
    from app.config import get_settings
    nodes = _create_node_functions(get_settings())
    return await nodes[3](state)


async def code_node(state: AgentState) -> dict:
    from app.config import get_settings
    nodes = _create_node_functions(get_settings())
    return await nodes[4](state)


async def execute_node(state: AgentState) -> dict:
    from app.config import get_settings
    nodes = _create_node_functions(get_settings())
    return await nodes[5](state)


async def review_node(state: AgentState) -> dict:
    from app.config import get_settings
    nodes = _create_node_functions(get_settings())
    return await nodes[6](state)


async def apply_fix_node(state: AgentState) -> dict:
    from app.config import get_settings
    nodes = _create_node_functions(get_settings())
    return await nodes[7](state)


async def finalize_node(state: AgentState) -> dict:
    from app.config import get_settings
    nodes = _create_node_functions(get_settings())
    return await nodes[8](state)


async def fail_node(state: AgentState) -> dict:
    from app.config import get_settings
    nodes = _create_node_functions(get_settings())
    return await nodes[9](state)
