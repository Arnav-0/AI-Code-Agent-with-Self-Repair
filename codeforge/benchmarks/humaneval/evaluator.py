"""HumanEval benchmark evaluator."""

from __future__ import annotations

import logging

from benchmarks.humaneval.loader import HumanEvalProblem

logger = logging.getLogger(__name__)


async def evaluate_solution(
    problem: HumanEvalProblem,
    generated_code: str,
    sandbox,
) -> bool:
    """Combine generated_code + test function + check() call, execute in sandbox.

    Returns True if exit_code == 0.
    """
    full_code = "\n".join([
        generated_code,
        "",
        problem.test,
        "",
        f"check({problem.entry_point})",
    ])

    try:
        result = await sandbox.execute_python(full_code)
        return result.exit_code == 0
    except Exception as exc:
        logger.warning("Sandbox error for %s: %s", problem.task_id, exc)
        return False


def calculate_pass_at_1(results: list[bool]) -> float:
    """Simple pass@1: fraction of problems that passed."""
    if not results:
        return 0.0
    return sum(results) / len(results)
