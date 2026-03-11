"""Tool-using conversational agent with ReAct-style loop."""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Optional

import httpx

from app.tools.base import ToolRegistry, ToolResult

logger = logging.getLogger("codeforge.tool_agent")


@dataclass
class AgentEvent:
    """Event emitted during agent execution.

    Types:
        thinking  - Agent's internal reasoning / text alongside tool calls
        tool_call - Agent is invoking a tool
        tool_result - Result from a tool execution
        text      - Final assistant text (no more tool calls this turn)
        error     - An error occurred
        done      - Agent loop finished
        agent_switch - Active agent role changed (multi-agent only)
    """

    type: str
    data: dict = field(default_factory=dict)


class ToolAgent:
    """ReAct-style agent that uses tools to accomplish tasks.

    Calls an OpenAI-compatible chat completions endpoint (OpenRouter) in a loop,
    executing tool calls and feeding results back until the model produces a
    final text response or the iteration limit is reached.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        tools: ToolRegistry,
        system_prompt: str,
        role: str = "main",
        max_iterations: int = 25,
        max_tool_calls_per_turn: int = 10,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.tools = tools
        self.system_prompt = system_prompt
        self.role = role
        self.max_iterations = max_iterations
        self.max_tool_calls_per_turn = max_tool_calls_per_turn
        self._cancelled = False

    def cancel(self) -> None:
        """Request graceful cancellation of the agent loop."""
        self._cancelled = True

    async def run(
        self, messages: list[dict], *, extra_context: Optional[str] = None,
    ) -> AsyncGenerator[AgentEvent, None]:
        """Run the agent loop, yielding events as they occur.

        Parameters
        ----------
        messages:
            Conversation history (user/assistant/tool messages).
        extra_context:
            Optional additional context appended to the system prompt for
            this run only (e.g. delegation instructions).
        """
        system_content = self.system_prompt
        if extra_context:
            system_content = f"{system_content}\n\n{extra_context}"

        full_messages: list[dict] = [
            {"role": "system", "content": system_content},
            *messages,
        ]

        tool_schemas = self.tools.to_openai_tools()
        total_tokens = 0

        for iteration in range(self.max_iterations):
            if self._cancelled:
                yield AgentEvent("error", {"error": "Agent cancelled"})
                return

            # ── Call LLM ────────────────────────────────────────────────
            try:
                response = await self._call_llm(full_messages, tool_schemas)
            except httpx.HTTPStatusError as exc:
                body = exc.response.text[:500] if exc.response else ""
                yield AgentEvent(
                    "error",
                    {"error": f"LLM API error ({exc.response.status_code}): {body}"},
                )
                return
            except Exception as exc:
                yield AgentEvent("error", {"error": f"LLM call failed: {exc}"})
                return

            choice = response.get("choices", [{}])[0]
            message = choice.get("message", {})
            usage = response.get("usage", {})
            total_tokens += usage.get("total_tokens", 0)

            # Add assistant message to conversation history
            full_messages.append(message)

            tool_calls = message.get("tool_calls")

            # ── No tool calls → final text response ─────────────────────
            if not tool_calls:
                content = message.get("content", "")
                if content:
                    yield AgentEvent(
                        "text", {"content": content, "role": self.role}
                    )
                yield AgentEvent(
                    "done",
                    {
                        "iterations": iteration + 1,
                        "total_tokens": total_tokens,
                        "role": self.role,
                    },
                )
                return

            # ── Emit thinking text if present alongside tool calls ──────
            if message.get("content"):
                yield AgentEvent(
                    "thinking",
                    {"content": message["content"], "role": self.role},
                )

            # ── Execute tool calls ──────────────────────────────────────
            calls_to_process = tool_calls[: self.max_tool_calls_per_turn]

            for tc in calls_to_process:
                if self._cancelled:
                    yield AgentEvent("error", {"error": "Agent cancelled"})
                    return

                fn = tc.get("function", {})
                tool_name = fn.get("name", "")
                try:
                    arguments = json.loads(fn.get("arguments", "{}"))
                except json.JSONDecodeError:
                    arguments = {}

                tc_id = tc.get("id", "")

                yield AgentEvent(
                    "tool_call",
                    {
                        "id": tc_id,
                        "name": tool_name,
                        "arguments": arguments,
                        "role": self.role,
                    },
                )

                # Execute the tool
                tool = self.tools.get(tool_name)
                if tool is not None:
                    try:
                        start = time.perf_counter()
                        result = await tool.execute(**arguments)
                        duration_ms = int(
                            (time.perf_counter() - start) * 1000
                        )
                        result.metadata["duration_ms"] = duration_ms
                    except Exception as exc:
                        result = ToolResult(
                            output="", error=str(exc), success=False
                        )
                else:
                    result = ToolResult(
                        output="",
                        error=f"Unknown tool: {tool_name}",
                        success=False,
                    )

                yield AgentEvent(
                    "tool_result",
                    {
                        "id": tc_id,
                        "name": tool_name,
                        "output": result.output[:10_000],
                        "error": result.error,
                        "success": result.success,
                        "duration_ms": result.metadata.get("duration_ms", 0),
                        "role": self.role,
                    },
                )

                # Append tool result to conversation for the next LLM call
                tool_content = (
                    result.output if result.success else f"Error: {result.error}"
                )
                full_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc_id,
                        "content": tool_content[:50_000],
                    }
                )

        # Exhausted iterations
        yield AgentEvent(
            "error",
            {
                "error": f"Max iterations ({self.max_iterations}) reached",
                "iterations": self.max_iterations,
                "total_tokens": total_tokens,
            },
        )

    # ── LLM API call ────────────────────────────────────────────────────

    async def _call_llm(
        self, messages: list[dict], tools: list[dict]
    ) -> dict:
        """Call OpenRouter chat completions API with tool support."""
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": self._sanitize_messages(messages),
            "temperature": 0.1,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://codeforge.dev",
                    "X-Title": "CodeForge Agent",
                },
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    def _sanitize_messages(messages: list[dict]) -> list[dict]:
        """Ensure messages are JSON-serializable for the API.

        Strips any non-serializable fields and ensures tool_calls are
        properly formatted dicts.
        """
        clean: list[dict] = []
        for msg in messages:
            m: dict[str, Any] = {"role": msg.get("role", "user")}

            if msg.get("content") is not None:
                m["content"] = msg["content"]

            if msg.get("tool_calls"):
                m["tool_calls"] = msg["tool_calls"]

            if msg.get("tool_call_id"):
                m["tool_call_id"] = msg["tool_call_id"]

            # For tool role, content is required
            if m["role"] == "tool" and "content" not in m:
                m["content"] = ""

            clean.append(m)
        return clean
