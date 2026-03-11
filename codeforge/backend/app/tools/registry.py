"""Default tool registry factory."""
from __future__ import annotations

from app.tools.base import ToolRegistry


def create_tool_registry(workspace_root: str) -> ToolRegistry:
    """Create a registry with all default tools scoped to workspace."""
    from app.tools.bash import RunCommandTool
    from app.tools.file_ops import (
        EditFileTool,
        ListDirectoryTool,
        ReadFileTool,
        WriteFileTool,
    )
    from app.tools.search import SearchContentTool, SearchFilesTool

    registry = ToolRegistry()
    registry.register(ReadFileTool(workspace_root))
    registry.register(WriteFileTool(workspace_root))
    registry.register(EditFileTool(workspace_root))
    registry.register(ListDirectoryTool(workspace_root))
    registry.register(SearchFilesTool(workspace_root))
    registry.register(SearchContentTool(workspace_root))
    registry.register(RunCommandTool(workspace_root))
    return registry
