"""Custom benchmark evaluator."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

TASKS_PATH = Path(__file__).parent / "tasks.json"


def load_custom_problems() -> list[dict]:
    """Load custom benchmark tasks from tasks.json."""
    with TASKS_PATH.open() as f:
        tasks = json.load(f)
    logger.info("Loaded %d custom benchmark tasks", len(tasks))
    return tasks


async def evaluate_custom_solution(
    problem: dict,
    generated_code: str,
    sandbox: Any,
) -> bool:
    """Combine generated_code + test assertions and execute in sandbox.

    Returns True if all assertions pass (exit_code == 0).
    """
    assertions = problem.get("test_assertions", [])
    if not assertions:
        logger.warning("Problem %s has no test assertions", problem.get("id"))
        return False

    parts = [generated_code, ""]
    for assertion in assertions:
        parts.append(assertion)

    full_code = "\n".join(parts)

    try:
        result = await sandbox.execute_python(full_code)
        return result.exit_code == 0
    except Exception as exc:
        logger.warning("Sandbox error for %s: %s", problem.get("id"), exc)
        return False


def calculate_pass_at_1(results: list[bool]) -> float:
    """Simple pass@1: fraction of problems that passed."""
    if not results:
        return 0.0
    return sum(results) / len(results)
