"""File operation tools: ReadFile, WriteFile, EditFile, ListDirectory."""
from __future__ import annotations

import logging
import os

from app.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)

# Limits
MAX_READ_LINES = 10_000
MAX_READ_BYTES = 50 * 1024  # 50 KB
MAX_WRITE_BYTES = 100 * 1024  # 100 KB


def _validate_path(workspace_root: str, requested_path: str) -> tuple[bool, str, str]:
    """Validate that a path is within workspace_root.

    Returns (is_valid, resolved_path, error_message).
    """
    try:
        root_real = os.path.realpath(workspace_root)
        # Resolve relative paths against workspace root
        if not os.path.isabs(requested_path):
            requested_path = os.path.join(workspace_root, requested_path)
        resolved = os.path.realpath(requested_path)
        if not resolved.startswith(root_real + os.sep) and resolved != root_real:
            return False, resolved, f"Path '{requested_path}' is outside workspace root"
        return True, resolved, ""
    except Exception as exc:
        return False, "", f"Path validation error: {exc}"


class ReadFileTool(BaseTool):
    """Read the contents of a file."""

    def __init__(self, workspace_root: str) -> None:
        self._workspace_root = workspace_root

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return (
            "Read the contents of a file. Returns numbered lines. "
            "Use offset and limit to read a specific range of lines."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path (absolute or relative to workspace root)",
                },
                "offset": {
                    "type": "integer",
                    "description": "Line number to start reading from (1-based, default 1)",
                },
                "limit": {
                    "type": "integer",
                    "description": (
                        f"Maximum number of lines to read (default {MAX_READ_LINES})"
                    ),
                },
            },
            "required": ["path"],
        }

    async def execute(self, **kwargs) -> ToolResult:
        path = kwargs.get("path", "")
        offset = max(kwargs.get("offset", 1), 1)
        limit = min(kwargs.get("limit", MAX_READ_LINES), MAX_READ_LINES)

        valid, resolved, err = _validate_path(self._workspace_root, path)
        if not valid:
            return ToolResult(output="", error=err, success=False)

        if not os.path.exists(resolved):
            return ToolResult(output="", error=f"File not found: {resolved}", success=False)

        if os.path.isdir(resolved):
            return ToolResult(
                output="", error=f"Path is a directory, not a file: {resolved}", success=False
            )

        try:
            file_size = os.path.getsize(resolved)
            if file_size > MAX_READ_BYTES:
                # Read up to limit but warn
                pass

            with open(resolved, encoding="utf-8", errors="replace") as f:
                lines = []
                bytes_read = 0
                for i, line in enumerate(f, start=1):
                    if i < offset:
                        continue
                    if len(lines) >= limit:
                        break
                    bytes_read += len(line.encode("utf-8", errors="replace"))
                    if bytes_read > MAX_READ_BYTES:
                        lines.append(f"  {i:>6}\t... [truncated at {MAX_READ_BYTES // 1024}KB]")
                        break
                    lines.append(f"  {i:>6}\t{line.rstrip()}")

            if not lines:
                return ToolResult(
                    output="(empty file or offset beyond end of file)",
                    metadata={"path": resolved, "lines": 0},
                )

            output = "\n".join(lines)
            return ToolResult(
                output=output,
                metadata={"path": resolved, "lines": len(lines)},
            )
        except Exception as exc:
            return ToolResult(output="", error=f"Error reading file: {exc}", success=False)


class WriteFileTool(BaseTool):
    """Create or overwrite a file."""

    def __init__(self, workspace_root: str) -> None:
        self._workspace_root = workspace_root

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return (
            "Create or overwrite a file with the given content. "
            "Parent directories are created automatically."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path (absolute or relative to workspace root)",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file",
                },
            },
            "required": ["path", "content"],
        }

    async def execute(self, **kwargs) -> ToolResult:
        path = kwargs.get("path", "")
        content = kwargs.get("content", "")

        valid, resolved, err = _validate_path(self._workspace_root, path)
        if not valid:
            return ToolResult(output="", error=err, success=False)

        content_bytes = content.encode("utf-8")
        if len(content_bytes) > MAX_WRITE_BYTES:
            return ToolResult(
                output="",
                error=f"Content exceeds maximum write size of {MAX_WRITE_BYTES // 1024}KB",
                success=False,
            )

        try:
            parent = os.path.dirname(resolved)
            os.makedirs(parent, exist_ok=True)

            with open(resolved, "w", encoding="utf-8") as f:
                f.write(content)

            line_count = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
            return ToolResult(
                output=f"Successfully wrote {len(content_bytes)} bytes to {resolved}",
                metadata={"path": resolved, "bytes": len(content_bytes), "lines": line_count},
            )
        except Exception as exc:
            return ToolResult(output="", error=f"Error writing file: {exc}", success=False)


class EditFileTool(BaseTool):
    """Edit a file by replacing an exact string match."""

    def __init__(self, workspace_root: str) -> None:
        self._workspace_root = workspace_root

    @property
    def name(self) -> str:
        return "edit_file"

    @property
    def description(self) -> str:
        return (
            "Edit a file by replacing an exact string with a new string. "
            "The old_string must appear exactly once in the file. "
            "Use this for surgical edits instead of rewriting the whole file."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path (absolute or relative to workspace root)",
                },
                "old_string": {
                    "type": "string",
                    "description": "The exact string to find and replace (must be unique in file)",
                },
                "new_string": {
                    "type": "string",
                    "description": "The replacement string",
                },
            },
            "required": ["path", "old_string", "new_string"],
        }

    async def execute(self, **kwargs) -> ToolResult:
        path = kwargs.get("path", "")
        old_string = kwargs.get("old_string", "")
        new_string = kwargs.get("new_string", "")

        if not old_string:
            return ToolResult(output="", error="old_string cannot be empty", success=False)

        valid, resolved, err = _validate_path(self._workspace_root, path)
        if not valid:
            return ToolResult(output="", error=err, success=False)

        if not os.path.exists(resolved):
            return ToolResult(output="", error=f"File not found: {resolved}", success=False)

        if os.path.isdir(resolved):
            return ToolResult(
                output="", error=f"Path is a directory, not a file: {resolved}", success=False
            )

        try:
            with open(resolved, encoding="utf-8", errors="replace") as f:
                content = f.read()

            occurrences = content.count(old_string)
            if occurrences == 0:
                return ToolResult(
                    output="",
                    error="old_string not found in file. Make sure it matches exactly.",
                    success=False,
                )
            if occurrences > 1:
                return ToolResult(
                    output="",
                    error=(
                        f"old_string found {occurrences} times in file. "
                        "It must be unique. Include more context to make it unique."
                    ),
                    success=False,
                )

            new_content = content.replace(old_string, new_string, 1)

            new_bytes = new_content.encode("utf-8")
            if len(new_bytes) > MAX_WRITE_BYTES:
                return ToolResult(
                    output="",
                    error=f"Resulting file exceeds maximum size of {MAX_WRITE_BYTES // 1024}KB",
                    success=False,
                )

            with open(resolved, "w", encoding="utf-8") as f:
                f.write(new_content)

            return ToolResult(
                output=f"Successfully edited {resolved}",
                metadata={"path": resolved},
            )
        except Exception as exc:
            return ToolResult(output="", error=f"Error editing file: {exc}", success=False)


class ListDirectoryTool(BaseTool):
    """List the contents of a directory."""

    def __init__(self, workspace_root: str) -> None:
        self._workspace_root = workspace_root

    @property
    def name(self) -> str:
        return "list_directory"

    @property
    def description(self) -> str:
        return (
            "List files and directories in a given directory. "
            "Shows type indicators: [file] or [dir] for each entry."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": (
                        "Directory path (absolute or relative to workspace root). "
                        "Defaults to workspace root if not provided."
                    ),
                },
            },
            "required": [],
        }

    async def execute(self, **kwargs) -> ToolResult:
        path = kwargs.get("path", self._workspace_root)
        if not path:
            path = self._workspace_root

        valid, resolved, err = _validate_path(self._workspace_root, path)
        if not valid:
            return ToolResult(output="", error=err, success=False)

        if not os.path.exists(resolved):
            return ToolResult(output="", error=f"Directory not found: {resolved}", success=False)

        if not os.path.isdir(resolved):
            return ToolResult(
                output="", error=f"Path is not a directory: {resolved}", success=False
            )

        try:
            entries = sorted(os.listdir(resolved))
            lines = []
            for entry in entries:
                full_path = os.path.join(resolved, entry)
                if os.path.isdir(full_path):
                    lines.append(f"  [dir]  {entry}/")
                else:
                    size = os.path.getsize(full_path)
                    lines.append(f"  [file] {entry} ({size} bytes)")

            if not lines:
                return ToolResult(
                    output="(empty directory)",
                    metadata={"path": resolved, "count": 0},
                )

            header = f"Directory: {resolved}\n"
            output = header + "\n".join(lines)
            return ToolResult(
                output=output,
                metadata={"path": resolved, "count": len(lines)},
            )
        except PermissionError:
            return ToolResult(
                output="", error=f"Permission denied: {resolved}", success=False
            )
        except Exception as exc:
            return ToolResult(
                output="", error=f"Error listing directory: {exc}", success=False
            )
