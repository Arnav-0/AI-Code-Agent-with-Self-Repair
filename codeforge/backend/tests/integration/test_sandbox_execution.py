"""Integration tests for sandbox execution. Requires Docker to be running."""
from __future__ import annotations

import pytest

from app.sandbox.manager import SandboxManager

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

TEST_IMAGE = "codeforge-sandbox-python:latest"


@pytest.fixture
def sandbox_manager(request):
    try:
        import docker  # type: ignore[import]
        client = docker.from_env()
        client.ping()
    except Exception:
        pytest.skip("Docker not available")

    # Check image exists
    try:
        client.images.get(TEST_IMAGE)
    except Exception:
        pytest.skip(f"Sandbox image '{TEST_IMAGE}' not built. Run: make build-sandbox")

    return SandboxManager(
        image=TEST_IMAGE,
        timeout=10,
        memory_mb=256,
        cpu_limit=1.0,
        network_disabled=True,
    )


async def test_execute_simple_print(sandbox_manager: SandboxManager) -> None:
    result = await sandbox_manager.execute('print("Hello CodeForge")')
    assert result.success is True
    assert result.exit_code == 0
    assert "Hello CodeForge" in result.stdout
    assert result.stderr == ""


async def test_execute_math_computation(sandbox_manager: SandboxManager) -> None:
    result = await sandbox_manager.execute("import math; print(math.factorial(10))")
    assert result.success is True
    assert "3628800" in result.stdout


async def test_execute_with_imports(sandbox_manager: SandboxManager) -> None:
    result = await sandbox_manager.execute(
        "import numpy as np; print(np.array([1,2,3]).sum())"
    )
    assert result.success is True
    assert "6" in result.stdout


async def test_execute_pandas(sandbox_manager: SandboxManager) -> None:
    result = await sandbox_manager.execute(
        'import pandas as pd; df = pd.DataFrame({"a": [1,2,3]}); print(df.shape)'
    )
    assert result.success is True
    assert "(3, 1)" in result.stdout


async def test_execute_syntax_error(sandbox_manager: SandboxManager) -> None:
    result = await sandbox_manager.execute("def foo(\n  print(42)")
    assert result.success is False
    assert result.exit_code != 0
    assert "SyntaxError" in result.stderr


async def test_execute_runtime_error(sandbox_manager: SandboxManager) -> None:
    result = await sandbox_manager.execute("x = 1/0")
    assert result.success is False
    assert "ZeroDivisionError" in result.stderr


async def test_execute_import_error(sandbox_manager: SandboxManager) -> None:
    result = await sandbox_manager.execute("import nonexistent_module_xyz")
    assert result.success is False
    assert "ModuleNotFoundError" in result.stderr


async def test_execute_timeout(sandbox_manager: SandboxManager) -> None:
    result = await sandbox_manager.execute("import time; time.sleep(60)")
    assert result.timed_out is True or result.execution_time_ms >= sandbox_manager.timeout * 1000


async def test_execute_stderr_capture(sandbox_manager: SandboxManager) -> None:
    result = await sandbox_manager.execute(
        'import sys; print("error msg", file=sys.stderr)'
    )
    assert "error msg" in result.stderr


async def test_execute_multiline_output(sandbox_manager: SandboxManager) -> None:
    result = await sandbox_manager.execute(
        'for i in range(5): print(f"line {i}")'
    )
    assert result.success is True
    for i in range(5):
        assert f"line {i}" in result.stdout


async def test_security_validation_blocks_dangerous_code(
    sandbox_manager: SandboxManager,
) -> None:
    result = await sandbox_manager.execute(
        'import subprocess; subprocess.run(["ls"])'
    )
    assert result.success is False
    assert "Security validation failed" in result.stderr


async def test_container_cleanup(sandbox_manager: SandboxManager) -> None:
    import docker  # type: ignore[import]

    result = await sandbox_manager.execute('print("cleanup test")')
    assert result.success is True

    container_id = result.container_id
    if container_id:
        client = docker.from_env()
        try:
            client.containers.get(container_id)
            # If we get here, container still exists — that's unexpected
            assert False, f"Container {container_id} still exists after execution"
        except docker.errors.NotFound:
            pass  # Expected: container was cleaned up


async def test_execute_large_output(sandbox_manager: SandboxManager) -> None:
    result = await sandbox_manager.execute('print("x" * 100000)')
    assert result.success is True
    assert len(result.stdout) > 0
