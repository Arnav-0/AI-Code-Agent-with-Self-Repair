"""Command execution tool: RunCommand."""
from __future__ import annotations

import asyncio
import logging
import os

from app.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)

# Limits
MAX_OUTPUT_BYTES = 50 * 1024  # 50 KB
DEFAULT_TIMEOUT = 30
MAX_TIMEOUT = 120

# Dangerous command patterns (blocklist)
BLOCKED_PATTERNS: list[str] = [
    "rm -rf /",
    "rm -rf /*",
    "mkfs",
    "dd if=",
    ":(){ :|:& };:",  # fork bomb
    "fork bomb",
    "> /dev/sda",
    "chmod -R 777 /",
    "chown -R",
    "shutdown",
    "reboot",
    "init 0",
    "init 6",
    "halt",
    "poweroff",
]


def _is_blocked(command: str) -> bool:
    """Check if a command matches any blocked pattern."""
    cmd_lower = command.lower().strip()
    for pattern in BLOCKED_PATTERNS:
        if pattern.lower() in cmd_lower:
            return True
    return False


def _safe_env(workspace_root: str) -> dict[str, str]:
    """Build a sanitized environment for subprocess execution."""
    env = {
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", "/tmp"),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "TERM": "dumb",
        "WORKSPACE_ROOT": workspace_root,
    }
    # Propagate PYTHONPATH if set
    pythonpath = os.environ.get("PYTHONPATH")
    if pythonpath:
        env["PYTHONPATH"] = pythonpath
    return env


def _truncate_output(text: str, max_bytes: int = MAX_OUTPUT_BYTES) -> str:
    """Truncate output to max_bytes, appending a truncation notice."""
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= max_bytes:
        return text
    truncated = encoded[:max_bytes].decode("utf-8", errors="replace")
    return truncated + f"\n... [output truncated at {max_bytes // 1024}KB]"


class RunCommandTool(BaseTool):
    """Execute a shell command in the workspace."""

    def __init__(self, workspace_root: str) -> None:
        self._workspace_root = workspace_root

    @property
    def name(self) -> str:
        return "run_command"

    @property
    def description(self) -> str:
        return (
            "Execute a shell command in the workspace directory. "
            "Returns stdout, stderr, and exit code. "
            f"Timeout defaults to {DEFAULT_TIMEOUT}s, max {MAX_TIMEOUT}s. "
            f"Output is truncated to {MAX_OUTPUT_BYTES // 1024}KB."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute",
                },
                "timeout": {
                    "type": "integer",
                    "description": (
                        f"Timeout in seconds (default {DEFAULT_TIMEOUT}, max {MAX_TIMEOUT})"
                    ),
                },
            },
            "required": ["command"],
        }

    async def execute(self, **kwargs) -> ToolResult:
        command = kwargs.get("command", "")
        timeout = kwargs.get("timeout", DEFAULT_TIMEOUT)

        if not command or not command.strip():
            return ToolResult(output="", error="command cannot be empty", success=False)

        # Enforce timeout bounds
        if not isinstance(timeout, int):
            try:
                timeout = int(timeout)
            except (TypeError, ValueError):
                timeout = DEFAULT_TIMEOUT
        timeout = max(1, min(timeout, MAX_TIMEOUT))

        # Check blocklist
        if _is_blocked(command):
            return ToolResult(
                output="",
                error=f"Command blocked for safety: {command}",
                success=False,
            )

        # Validate workspace root exists
        ws_real = os.path.realpath(self._workspace_root)
        if not os.path.isdir(ws_real):
            return ToolResult(
                output="",
                error=f"Workspace directory not found: {ws_real}",
                success=False,
            )

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=ws_real,
                env=_safe_env(ws_real),
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult(
                    output="",
                    error=f"Command timed out after {timeout}s",
                    success=False,
                    metadata={"exit_code": -1, "timed_out": True},
                )

            stdout = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
            stderr = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""
            exit_code = process.returncode or 0

            stdout = _truncate_output(stdout)
            stderr = _truncate_output(stderr)

            success = exit_code == 0

            # Build output
            parts: list[str] = []
            if stdout:
                parts.append(stdout)
            if stderr:
                parts.append(f"[stderr]\n{stderr}")
            parts.append(f"[exit code: {exit_code}]")

            return ToolResult(
                output="\n".join(parts),
                error=stderr if not success else "",
                success=success,
                metadata={"exit_code": exit_code},
            )
        except Exception as exc:
            return ToolResult(
                output="", error=f"Error executing command: {exc}", success=False
            )
