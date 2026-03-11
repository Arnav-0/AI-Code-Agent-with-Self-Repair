from __future__ import annotations

import logging

from app.sandbox.manager import ExecutionOutput, SandboxManager

logger = logging.getLogger(__name__)

_docker_available: bool | None = None


def _check_docker() -> bool:
    """Check if Docker is available on this system (cached)."""
    global _docker_available
    if _docker_available is not None:
        return _docker_available
    try:
        import docker  # type: ignore[import]

        client = docker.from_env()
        client.ping()
        _docker_available = True
    except Exception:
        logger.info("Docker not available — using local subprocess executor")
        _docker_available = False
    return _docker_available


class CodeExecutor:
    def __init__(self, settings) -> None:
        self._settings = settings
        self._docker_executor: SandboxManager | None = None
        self._local_executor = None

    def _get_executor(self):
        if _check_docker():
            if self._docker_executor is None:
                self._docker_executor = SandboxManager(
                    image=self._settings.sandbox_image,
                    timeout=self._settings.sandbox_timeout_seconds,
                    memory_mb=self._settings.sandbox_memory_limit_mb,
                    cpu_limit=self._settings.sandbox_cpu_limit,
                    network_disabled=self._settings.sandbox_network_disabled,
                )
            return self._docker_executor
        else:
            if self._local_executor is None:
                from app.sandbox.local_executor import LocalExecutor

                self._local_executor = LocalExecutor(
                    timeout=self._settings.sandbox_timeout_seconds,
                    memory_mb=self._settings.sandbox_memory_limit_mb,
                )
            return self._local_executor

    async def execute_python(self, code: str) -> ExecutionOutput:
        executor = self._get_executor()
        return await executor.execute(code, language="python")

    async def execute_with_retry(
        self, code: str, max_retries: int = 0
    ) -> ExecutionOutput:
        """Single attempt execution. Retries are managed by the orchestrator."""
        return await self.execute_python(code)
