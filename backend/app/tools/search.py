"""Search tools: SearchFiles (glob) and SearchContent (grep)."""
from __future__ import annotations

import logging
import os
import re
from pathlib import Path

from app.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)

# Limits
MAX_GLOB_RESULTS = 100
MAX_GREP_FILES = 50
MAX_GREP_MATCHES = 200


def _validate_path(workspace_root: str, requested_path: str) -> tuple[bool, str, str]:
    """Validate that a path is within workspace_root.

    Returns (is_valid, resolved_path, error_message).
    """
    try:
        root_real = os.path.realpath(workspace_root)
        if not os.path.isabs(requested_path):
            requested_path = os.path.join(workspace_root, requested_path)
        resolved = os.path.realpath(requested_path)
        if not resolved.startswith(root_real + os.sep) and resolved != root_real:
            return False, resolved, f"Path '{requested_path}' is outside workspace root"
        return True, resolved, ""
    except Exception as exc:
        return False, "", f"Path validation error: {exc}"


class SearchFilesTool(BaseTool):
    """Search for files using glob patterns."""

    def __init__(self, workspace_root: str) -> None:
        self._workspace_root = workspace_root

    @property
    def name(self) -> str:
        return "search_files"

    @property
    def description(self) -> str:
        return (
            "Search for files using glob patterns (e.g., '**/*.py', 'src/**/*.ts'). "
            f"Returns up to {MAX_GLOB_RESULTS} matching file paths."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern to match files (e.g., '**/*.py', '*.json')",
                },
                "path": {
                    "type": "string",
                    "description": (
                        "Directory to search in (relative to workspace root). "
                        "Defaults to workspace root."
                    ),
                },
            },
            "required": ["pattern"],
        }

    async def execute(self, **kwargs) -> ToolResult:
        pattern = kwargs.get("pattern", "")
        path = kwargs.get("path", "")

        if not pattern:
            return ToolResult(output="", error="pattern is required", success=False)

        if path:
            valid, resolved, err = _validate_path(self._workspace_root, path)
            if not valid:
                return ToolResult(output="", error=err, success=False)
            search_root = resolved
        else:
            search_root = os.path.realpath(self._workspace_root)

        if not os.path.isdir(search_root):
            return ToolResult(
                output="", error=f"Search directory not found: {search_root}", success=False
            )

        try:
            root_path = Path(search_root)
            matches = []
            for match in root_path.glob(pattern):
                # Ensure match is within workspace
                match_real = os.path.realpath(str(match))
                ws_real = os.path.realpath(self._workspace_root)
                if not match_real.startswith(ws_real + os.sep) and match_real != ws_real:
                    continue
                # Show path relative to workspace root
                try:
                    rel = os.path.relpath(match_real, ws_real)
                except ValueError:
                    rel = match_real
                matches.append(rel)
                if len(matches) >= MAX_GLOB_RESULTS:
                    break

            if not matches:
                return ToolResult(
                    output="No files matched the pattern.",
                    metadata={"pattern": pattern, "count": 0},
                )

            truncated = ""
            if len(matches) >= MAX_GLOB_RESULTS:
                truncated = f"\n... (truncated at {MAX_GLOB_RESULTS} results)"

            output = "\n".join(matches) + truncated
            return ToolResult(
                output=output,
                metadata={"pattern": pattern, "count": len(matches)},
            )
        except Exception as exc:
            return ToolResult(
                output="", error=f"Error searching files: {exc}", success=False
            )


class SearchContentTool(BaseTool):
    """Search file contents using regex patterns."""

    def __init__(self, workspace_root: str) -> None:
        self._workspace_root = workspace_root

    @property
    def name(self) -> str:
        return "search_content"

    @property
    def description(self) -> str:
        return (
            "Search file contents using a regex pattern (like grep). "
            "Returns matching lines with file:line_number:content format. "
            f"Searches up to {MAX_GREP_FILES} files, returns up to {MAX_GREP_MATCHES} matches."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Regex pattern to search for in file contents",
                },
                "path": {
                    "type": "string",
                    "description": (
                        "Directory to search in (relative to workspace root). "
                        "Defaults to workspace root."
                    ),
                },
                "file_pattern": {
                    "type": "string",
                    "description": (
                        "Glob pattern to filter which files to search "
                        "(e.g., '*.py', '*.ts'). Defaults to all files."
                    ),
                },
            },
            "required": ["pattern"],
        }

    async def execute(self, **kwargs) -> ToolResult:
        pattern = kwargs.get("pattern", "")
        path = kwargs.get("path", "")
        file_pattern = kwargs.get("file_pattern", "")

        if not pattern:
            return ToolResult(output="", error="pattern is required", success=False)

        # Validate regex
        try:
            regex = re.compile(pattern)
        except re.error as exc:
            return ToolResult(
                output="", error=f"Invalid regex pattern: {exc}", success=False
            )

        if path:
            valid, resolved, err = _validate_path(self._workspace_root, path)
            if not valid:
                return ToolResult(output="", error=err, success=False)
            search_root = resolved
        else:
            search_root = os.path.realpath(self._workspace_root)

        if not os.path.isdir(search_root):
            return ToolResult(
                output="", error=f"Search directory not found: {search_root}", success=False
            )

        try:
            ws_real = os.path.realpath(self._workspace_root)
            root_path = Path(search_root)

            # Collect files to search
            if file_pattern:
                file_iter = root_path.rglob(file_pattern)
            else:
                file_iter = root_path.rglob("*")

            files_to_search: list[Path] = []
            for fp in file_iter:
                if not fp.is_file():
                    continue
                # Skip binary-looking files and common non-text directories
                if any(
                    part in fp.parts
                    for part in (
                        ".git", "__pycache__", "node_modules", ".venv",
                        "venv", ".mypy_cache", ".ruff_cache",
                    )
                ):
                    continue
                fp_real = os.path.realpath(str(fp))
                if not fp_real.startswith(ws_real + os.sep) and fp_real != ws_real:
                    continue
                files_to_search.append(fp)
                if len(files_to_search) >= MAX_GREP_FILES:
                    break

            matches: list[str] = []
            files_with_matches = 0

            for fp in files_to_search:
                try:
                    with open(fp, encoding="utf-8", errors="replace") as f:
                        file_had_match = False
                        for line_num, line in enumerate(f, start=1):
                            if regex.search(line):
                                try:
                                    rel = os.path.relpath(str(fp), ws_real)
                                except ValueError:
                                    rel = str(fp)
                                matches.append(
                                    f"{rel}:{line_num}:{line.rstrip()}"
                                )
                                file_had_match = True
                                if len(matches) >= MAX_GREP_MATCHES:
                                    break
                        if file_had_match:
                            files_with_matches += 1
                except (PermissionError, OSError):
                    # Skip files we cannot read
                    continue

                if len(matches) >= MAX_GREP_MATCHES:
                    break

            if not matches:
                return ToolResult(
                    output="No matches found.",
                    metadata={"pattern": pattern, "count": 0, "files": 0},
                )

            truncated = ""
            if len(matches) >= MAX_GREP_MATCHES:
                truncated = f"\n... (truncated at {MAX_GREP_MATCHES} matches)"

            output = "\n".join(matches) + truncated
            return ToolResult(
                output=output,
                metadata={
                    "pattern": pattern,
                    "count": len(matches),
                    "files": files_with_matches,
                },
            )
        except Exception as exc:
            return ToolResult(
                output="", error=f"Error searching content: {exc}", success=False
            )
