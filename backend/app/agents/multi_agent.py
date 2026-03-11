"""Multi-agent orchestrator that delegates tasks to specialist agents."""
from __future__ import annotations

import logging
from typing import AsyncGenerator

from app.agents.prompts.tool_agent import ROLE_PROMPTS
from app.agents.tool_agent import AgentEvent, ToolAgent
from app.tools.base import BaseTool, ToolRegistry, ToolResult

logger = logging.getLogger("codeforge.multi_agent")


# ── Delegate meta-tools ────────────────────────────────────────────────────


class DelegateTool(BaseTool):
    """Meta-tool that delegates a task to a specialist ToolAgent.

    When the orchestrator calls this tool, it spins up the specialist agent,
    collects all its events, and returns the final text as the tool result.
    Events from the specialist are buffered and can be retrieved via
    ``pop_events()``.
    """

    def __init__(
        self,
        target_role: str,
        agent_factory: "_AgentFactory",
    ) -> None:
        self._target_role = target_role
        self._agent_factory = agent_factory
        self._buffered_events: list[AgentEvent] = []

    @property
    def name(self) -> str:
        return f"delegate_to_{self._target_role}"

    @property
    def description(self) -> str:
        role_descs = {
            "explorer": (
                "Delegate a code-exploration task to the Explorer agent. "
                "The explorer reads files, searches code, and maps project "
                "structure. It never modifies files. Returns its findings."
            ),
            "coder": (
                "Delegate a coding task to the Coder agent. "
                "The coder implements features, fixes bugs, and refactors "
                "code. It reads, edits, and writes files, then runs tests. "
                "Returns a summary of changes made."
            ),
            "tester": (
                "Delegate a testing task to the Tester agent. "
                "The tester writes and runs tests, analyzes failures, and "
                "verifies correctness. Returns test results and coverage."
            ),
            "reviewer": (
                "Delegate a code-review task to the Reviewer agent. "
                "The reviewer analyzes code for bugs, security issues, and "
                "style problems. Returns specific, actionable feedback."
            ),
        }
        return role_descs.get(
            self._target_role,
            f"Delegate a task to the {self._target_role} specialist agent.",
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": (
                        "A clear, specific description of what the specialist "
                        "agent should do. Include relevant file paths, function "
                        "names, or context the agent will need."
                    ),
                },
            },
            "required": ["task"],
        }

    def pop_events(self) -> list[AgentEvent]:
        """Return and clear buffered events from the last execution."""
        events = list(self._buffered_events)
        self._buffered_events.clear()
        return events

    async def execute(self, **kwargs) -> ToolResult:
        task_description = kwargs.get("task", "")
        if not task_description:
            return ToolResult(
                output="", error="Task description is required", success=False
            )

        self._buffered_events.clear()

        agent = self._agent_factory.create(self._target_role)
        messages = [{"role": "user", "content": task_description}]

        final_text = ""
        total_tokens = 0
        iterations = 0

        try:
            async for event in agent.run(messages):
                self._buffered_events.append(event)
                if event.type == "text":
                    final_text = event.data.get("content", "")
                elif event.type == "done":
                    total_tokens = event.data.get("total_tokens", 0)
                    iterations = event.data.get("iterations", 0)
                elif event.type == "error":
                    return ToolResult(
                        output="",
                        error=event.data.get("error", "Unknown agent error"),
                        success=False,
                    )
        except Exception as exc:
            return ToolResult(
                output="", error=f"Delegate agent failed: {exc}", success=False
            )

        if not final_text:
            final_text = "(Agent completed without producing text output)"

        return ToolResult(
            output=final_text,
            metadata={
                "role": self._target_role,
                "total_tokens": total_tokens,
                "iterations": iterations,
            },
        )


class _AgentFactory:
    """Creates specialist ToolAgent instances with the correct prompts/tools."""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_tools: ToolRegistry,
        max_iterations: int = 15,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_tools = base_tools
        self.max_iterations = max_iterations

    def create(self, role: str) -> ToolAgent:
        prompt = ROLE_PROMPTS.get(role, ROLE_PROMPTS["main"])
        return ToolAgent(
            api_key=self.api_key,
            model=self.model,
            tools=self.base_tools,
            system_prompt=prompt,
            role=role,
            max_iterations=self.max_iterations,
        )


# ── Multi-agent orchestrator ───────────────────────────────────────────────


class MultiAgent:
    """Orchestrator that has direct tool access plus delegation meta-tools.

    For simple tasks the orchestrator uses tools directly. For complex tasks
    it delegates to specialist agents (explorer, coder, tester, reviewer)
    via the ``delegate_to_*`` meta-tools.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        base_tools: ToolRegistry,
        max_iterations: int = 25,
        specialist_max_iterations: int = 15,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self._cancelled = False

        # Build agent factory for specialists
        self._factory = _AgentFactory(
            api_key=api_key,
            model=model,
            base_tools=base_tools,
            max_iterations=specialist_max_iterations,
        )

        # Build the orchestrator's tool registry: base tools + delegate tools
        self._orchestrator_tools = ToolRegistry()
        for tool in base_tools.all_tools():
            self._orchestrator_tools.register(tool)

        self._delegate_tools: dict[str, DelegateTool] = {}
        for role in ("explorer", "coder", "tester", "reviewer"):
            dt = DelegateTool(target_role=role, agent_factory=self._factory)
            self._delegate_tools[role] = dt
            self._orchestrator_tools.register(dt)

        # Create the main orchestrator agent
        self._orchestrator = ToolAgent(
            api_key=api_key,
            model=model,
            tools=self._orchestrator_tools,
            system_prompt=ROLE_PROMPTS["main"],
            role="main",
            max_iterations=max_iterations,
        )

    def cancel(self) -> None:
        """Cancel the orchestrator and any running specialists."""
        self._cancelled = True
        self._orchestrator.cancel()

    async def run(
        self, messages: list[dict]
    ) -> AsyncGenerator[AgentEvent, None]:
        """Run the multi-agent loop, yielding all events.

        Events from specialist agents are interleaved with orchestrator events.
        ``agent_switch`` events are emitted when control passes between agents.
        """
        current_role = "main"

        async for event in self._orchestrator.run(messages):
            if self._cancelled:
                yield AgentEvent("error", {"error": "Multi-agent cancelled"})
                return

            # If a delegate tool was called, emit its buffered events
            if event.type == "tool_result":
                tool_name = event.data.get("name", "")
                for role, dt in self._delegate_tools.items():
                    if tool_name == dt.name:
                        # Emit agent_switch to specialist
                        yield AgentEvent(
                            "agent_switch",
                            {"from": current_role, "to": role},
                        )
                        current_role = role

                        # Yield all buffered specialist events
                        for sub_event in dt.pop_events():
                            yield sub_event

                        # Switch back to main
                        yield AgentEvent(
                            "agent_switch",
                            {"from": role, "to": "main"},
                        )
                        current_role = "main"
                        break

            yield event
