from __future__ import annotations

import asyncio
import logging
import os
import tempfile
import time
from dataclasses import dataclass
from typing import Optional
from uuid import uuid4

from app.sandbox.security import validate_code

logger = logging.getLogger(__name__)

MAX_OUTPUT_BYTES = 512 * 1024  # 512 KB max per stream


@dataclass
class ExecutionOutput:
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    execution_time_ms: int
    memory_used_mb: Optional[float]
    container_id: str
    timed_out: bool = False


class SandboxManager:
    def __init__(
        self,
        image: str,
        timeout: int = 30,
        memory_mb: int = 512,
        cpu_limit: float = 1.0,
        network_disabled: bool = True,
    ) -> None:
        self.image = image
        self.timeout = timeout
        self.memory_mb = memory_mb
        self.cpu_limit = cpu_limit
        self.network_disabled = network_disabled

    def _get_docker_client(self):
        import docker  # type: ignore[import]

        return docker.from_env()

    async def create_container(self, code: str, language: str = "python") -> tuple[str, str]:
        """Create a container for code execution. Returns (container_id, temp_dir)."""
        temp_dir = tempfile.mkdtemp(prefix="codeforge_")
        filename = "main.py" if language == "python" else "main.js"
        code_path = os.path.join(temp_dir, filename)

        with open(code_path, "w") as f:
            f.write(code)

        container_name = f"codeforge-sandbox-{uuid4().hex[:8]}"

        def _create() -> str:
            client = self._get_docker_client()
            container = client.containers.create(
                image=self.image,
                name=container_name,
                volumes={temp_dir: {"bind": "/code", "mode": "ro"}},
                command=["/code/" + filename],
                mem_limit=f"{self.memory_mb}m",
                nano_cpus=int(self.cpu_limit * 1_000_000_000),
                network_disabled=self.network_disabled,
                user="sandbox",
                read_only=True,
                tmpfs={"/tmp": "size=64M"},
                working_dir="/code",
            )
            return container.id

        container_id = await asyncio.to_thread(_create)
        logger.info(f"Container created: {container_id[:12]}")
        return container_id, temp_dir

    async def execute(self, code: str, language: str = "python") -> ExecutionOutput:
        # Soft security check first
        is_safe, reason = validate_code(code)
        if not is_safe:
            return ExecutionOutput(
                success=False,
                exit_code=1,
                stdout="",
                stderr=f"Security validation failed: {reason}",
                execution_time_ms=0,
                memory_used_mb=None,
                container_id="",
            )

        container_id = ""
        temp_dir = ""
        timed_out = False

        def _run_container() -> tuple[int, str, str, Optional[float]]:
            nonlocal container_id, temp_dir, timed_out
            client = self._get_docker_client()

            # Get pre-created container or create inline
            temp_dir_local = tempfile.mkdtemp(prefix="codeforge_")
            filename = "main.py" if language == "python" else "main.js"
            code_path = os.path.join(temp_dir_local, filename)
            with open(code_path, "w") as f:
                f.write(code)

            cname = f"codeforge-sandbox-{uuid4().hex[:8]}"
            try:
                container = client.containers.create(
                    image=self.image,
                    name=cname,
                    volumes={temp_dir_local: {"bind": "/code", "mode": "ro"}},
                    command=["/code/" + filename],
                    mem_limit=f"{self.memory_mb}m",
                    nano_cpus=int(self.cpu_limit * 1_000_000_000),
                    network_disabled=self.network_disabled,
                    user="sandbox",
                    read_only=True,
                    tmpfs={"/tmp": "size=64M"},
                    working_dir="/code",
                )
                container_id = container.id
                container.start()

                try:
                    result = container.wait(timeout=self.timeout)
                    exit_code = result.get("StatusCode", 1)
                except Exception:
                    timed_out = True
                    exit_code = -1
                    try:
                        container.stop(timeout=2)
                    except Exception:
                        pass

                stdout_raw = container.logs(stdout=True, stderr=False)
                stderr_raw = container.logs(stdout=False, stderr=True)
                if len(stdout_raw) > MAX_OUTPUT_BYTES:
                    stdout_raw = stdout_raw[:MAX_OUTPUT_BYTES] + f"\n\n... [stdout truncated at {MAX_OUTPUT_BYTES // 1024} KB]".encode()
                if len(stderr_raw) > MAX_OUTPUT_BYTES:
                    stderr_raw = stderr_raw[:MAX_OUTPUT_BYTES] + f"\n\n... [stderr truncated at {MAX_OUTPUT_BYTES // 1024} KB]".encode()
                stdout_logs = stdout_raw.decode("utf-8", errors="replace")
                stderr_logs = stderr_raw.decode("utf-8", errors="replace")

                memory_mb: Optional[float] = None
                try:
                    stats = container.stats(stream=False)
                    mem_usage = stats.get("memory_stats", {}).get("usage", 0)
                    if mem_usage:
                        memory_mb = mem_usage / (1024 * 1024)
                except Exception:
                    pass

                return exit_code, stdout_logs, stderr_logs, memory_mb

            finally:
                try:
                    container.remove(force=True)
                except Exception:
                    pass
                import shutil
                shutil.rmtree(temp_dir_local, ignore_errors=True)

        start_time = time.monotonic()
        try:
            exit_code, stdout, stderr, memory_mb = await asyncio.wait_for(
                asyncio.to_thread(_run_container),
                timeout=self.timeout + 5,
            )
        except asyncio.TimeoutError:
            timed_out = True
            exit_code = -1
            stdout = ""
            stderr = "Execution timed out"
            memory_mb = None

        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        return ExecutionOutput(
            success=exit_code == 0,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            execution_time_ms=elapsed_ms,
            memory_used_mb=memory_mb,
            container_id=container_id,
            timed_out=timed_out,
        )

    async def cleanup_container(self, container_id: str) -> None:
        def _cleanup() -> None:
            import docker  # type: ignore[import]
            import docker.errors  # type: ignore[import]

            client = self._get_docker_client()
            try:
                container = client.containers.get(container_id)
                try:
                    container.stop(timeout=5)
                except Exception:
                    pass
                container.remove(force=True)
                logger.info(f"Container cleaned up: {container_id[:12]}")
            except docker.errors.NotFound:
                pass

        await asyncio.to_thread(_cleanup)
