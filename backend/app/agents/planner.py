"""Planner agent — decomposes tasks into subtask execution plans."""

from __future__ import annotations

import logging

from app.agents.base import AgentInput, AgentOutput, AgentType, BaseAgent
from app.agents.prompts.planner import PLANNER_SYSTEM_PROMPT, build_planner_user_prompt

logger = logging.getLogger("codeforge.agent.planner")


class PlannerAgent(BaseAgent):
    @property
    def agent_type(self) -> AgentType:
        return AgentType.PLANNER

    def _build_system_prompt(self) -> str:
        return PLANNER_SYSTEM_PROMPT

    def _build_user_prompt(self, input_data: AgentInput) -> str:
        return build_planner_user_prompt(input_data.data["prompt"])

    async def _execute(self, input_data: AgentInput) -> AgentOutput:
        user_prompt = self._build_user_prompt(input_data)
        response = await self._call_llm(user_prompt, structured=True)

        content = getattr(response, "content", "")
        plan = self._parse_json_response(content)

        valid, error_msg = self._validate_plan(plan)
        if not valid:
            # Retry once with error feedback
            retry_prompt = (
                f"{user_prompt}\n\nYour previous response had an error: {error_msg}\n"
                "Please fix and return valid JSON only."
            )
            response = await self._call_llm(retry_prompt, structured=True)
            content = getattr(response, "content", "")
            plan = self._parse_json_response(content)
            valid, error_msg = self._validate_plan(plan)
            if not valid:
                raise ValueError(f"Planner produced invalid plan: {error_msg}")

        tokens = getattr(response, "total_tokens", 0)
        rec = self.cost_tracker.record(response) if hasattr(self.cost_tracker, "record") else None
        cost = rec.cost_usd if rec else 0.0

        return AgentOutput(
            data=plan,
            reasoning=plan.get("reasoning", ""),
            tokens_used=tokens,
            cost_usd=cost,
            duration_ms=0,  # Set by run()
            success=True,
        )

    def _validate_plan(self, plan: dict) -> tuple[bool, str]:
        """Validate plan structure and dependencies."""
        if "subtasks" not in plan:
            return (False, "Missing 'subtasks' key")
        subtasks = plan["subtasks"]
        if not isinstance(subtasks, list) or len(subtasks) == 0:
            return (False, "'subtasks' must be a non-empty list")

        valid_ids = set()
        for i, st in enumerate(subtasks):
            for key in ("id", "description", "dependencies", "estimated_complexity"):
                if key not in st:
                    return (False, f"Subtask {i} missing key '{key}'")
            sid = st["id"]
            if not isinstance(sid, int):
                return (False, f"Subtask id must be int, got {type(sid)}")
            if sid in valid_ids:
                return (False, f"Duplicate subtask id: {sid}")
            valid_ids.add(sid)

        # Check dependencies reference valid IDs and no self-deps
        for st in subtasks:
            sid = st["id"]
            for dep in st.get("dependencies", []):
                if dep not in valid_ids:
                    return (False, f"Subtask {sid} depends on unknown id {dep}")
                if dep == sid:
                    return (False, f"Subtask {sid} depends on itself")

        # Topological sort to detect cycles
        if not self._is_dag(subtasks):
            return (False, "Circular dependency detected in subtasks")

        return (True, "")

    def _is_dag(self, subtasks: list[dict]) -> bool:
        """Return True if subtasks form a DAG (no cycles)."""
        graph: dict[int, list[int]] = {}
        for st in subtasks:
            graph[st["id"]] = list(st.get("dependencies", []))

        # Kahn's algorithm
        in_degree: dict[int, int] = {sid: 0 for sid in graph}
        for deps in graph.values():
            for dep in deps:
                in_degree[dep] = in_degree.get(dep, 0)  # ensure exists

        # Recalculate: edges go dep -> sid (dep must come before sid)
        # in_degree counts how many unsatisfied deps each node has
        in_deg: dict[int, int] = {sid: len(deps) for sid, deps in graph.items()}
        queue = [sid for sid, deg in in_deg.items() if deg == 0]
        visited = 0
        while queue:
            node = queue.pop(0)
            visited += 1
            # Find all nodes that depend on `node`
            for sid, deps in graph.items():
                if node in deps:
                    in_deg[sid] -= 1
                    if in_deg[sid] == 0:
                        queue.append(sid)

        return visited == len(graph)
