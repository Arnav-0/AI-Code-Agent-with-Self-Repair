"""Local subprocess-based code executor — fallback when Docker is unavailable."""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import tempfile
import time

from app.sandbox.manager import ExecutionOutput
from app.sandbox.security import validate_code

logger = logging.getLogger("codeforge.sandbox.local")

MAX_OUTPUT_BYTES = 512 * 1024  # 512 KB max per stream


def _truncate(data: bytes, label: str) -> bytes:
    if len(data) <= MAX_OUTPUT_BYTES:
        return data
    return data[:MAX_OUTPUT_BYTES] + f"\n\n... [{label} truncated at {MAX_OUTPUT_BYTES // 1024} KB]".encode()


class LocalExecutor:
    """Execute Python code in a subprocess with timeout enforcement.

    Used when Docker is not available. Provides process-level isolation
    via a temp directory and timeout, but NOT container-level sandboxing.
    """

    def __init__(self, timeout: int = 30, memory_mb: int = 512) -> None:
        self.timeout = timeout
        self.memory_mb = memory_mb

    async def execute(self, code: str, language: str = "python") -> ExecutionOutput:
        # Security check
        is_safe, reason = validate_code(code)
        if not is_safe:
            return ExecutionOutput(
                success=False,
                exit_code=1,
                stdout="",
                stderr=f"Security validation failed: {reason}",
                execution_time_ms=0,
                memory_used_mb=None,
                container_id="local",
            )

        if not code.strip():
            return ExecutionOutput(
                success=True,
                exit_code=0,
                stdout="",
                stderr="",
                execution_time_ms=0,
                memory_used_mb=None,
                container_id="local",
            )

        temp_dir = tempfile.mkdtemp(prefix="codeforge_local_")
        code_path = os.path.join(temp_dir, "main.py")
        try:
            with open(code_path, "w") as f:
                f.write(code)

            start = time.monotonic()
            timed_out = False
            try:
                proc = await asyncio.create_subprocess_exec(
                    "python3", code_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=temp_dir,
                )
                try:
                    stdout_bytes, stderr_bytes = await asyncio.wait_for(
                        proc.communicate(), timeout=self.timeout
                    )
                except asyncio.TimeoutError:
                    timed_out = True
                    proc.kill()
                    stdout_bytes, stderr_bytes = await proc.communicate()

            except FileNotFoundError:
                # python3 not found
                elapsed_ms = int((time.monotonic() - start) * 1000)
                return ExecutionOutput(
                    success=False,
                    exit_code=127,
                    stdout="",
                    stderr="python3 not found on system",
                    execution_time_ms=elapsed_ms,
                    memory_used_mb=None,
                    container_id="local",
                )

            elapsed_ms = int((time.monotonic() - start) * 1000)
            stdout = _truncate(stdout_bytes, "stdout").decode("utf-8", errors="replace")
            stderr = _truncate(stderr_bytes, "stderr").decode("utf-8", errors="replace")
            exit_code = -1 if timed_out else (proc.returncode or 0)

            if timed_out:
                stderr = f"Execution timed out after {self.timeout}s\n{stderr}"

            return ExecutionOutput(
                success=exit_code == 0 and not timed_out,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                execution_time_ms=elapsed_ms,
                memory_used_mb=None,
                container_id="local",
                timed_out=timed_out,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
