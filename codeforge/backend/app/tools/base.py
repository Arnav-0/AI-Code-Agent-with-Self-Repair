"""Base tool system for the multi-agent conversational pipeline."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ToolResult:
    """Result from executing a tool."""

    output: str
    error: str = ""
    success: bool = True
    metadata: dict = field(default_factory=dict)


@dataclass
class ToolCall:
    """Represents a tool call from the LLM."""

    id: str
    tool_name: str
    arguments: dict
    result: Optional[ToolResult] = None


class BaseTool(ABC):
    """Abstract base for all tools."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @property
    @abstractmethod
    def parameters(self) -> dict: ...

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult: ...

    def to_openai_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    """Registry of available tools."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def all_tools(self) -> list[BaseTool]:
        return list(self._tools.values())

    def to_openai_tools(self) -> list[dict]:
        return [t.to_openai_schema() for t in self._tools.values()]

    def tool_names(self) -> list[str]:
        return list(self._tools.keys())
