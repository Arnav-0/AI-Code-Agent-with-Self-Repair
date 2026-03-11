"""MBPP benchmark evaluator."""

from __future__ import annotations

import logging

from benchmarks.mbpp.loader import MBPPProblem

logger = logging.getLogger(__name__)


async def evaluate_solution(
    problem: MBPPProblem,
    generated_code: str,
    sandbox,
) -> bool:
    """Combine setup + generated_code + assertions, execute in sandbox.

    Returns True if exit_code == 0.
    """
    parts = []
    if problem.test_setup_code:
        parts.append(problem.test_setup_code)
    parts.append(generated_code)
    for assertion in problem.test_list:
        parts.append(assertion)

    full_code = "\n".join(parts)

    try:
        result = await sandbox.execute_python(full_code)
        return result.exit_code == 0
    except Exception as exc:
        logger.warning("Sandbox error for task_id %d: %s", problem.task_id, exc)
        return False


def calculate_pass_at_1(results: list[bool]) -> float:
    """Simple pass@1: fraction of problems that passed."""
    if not results:
        return 0.0
    return sum(results) / len(results)
