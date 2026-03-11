"""Benchmark runner — orchestrates HumanEval, MBPP, and custom evaluations."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

RESULTS_DIR = Path(__file__).parent / "results"


@dataclass
class ProblemResult:
    problem_id: str
    passed: bool
    retries_used: int
    cost_usd: float
    time_seconds: float
    generated_code: str = ""
    error_message: str = ""


@dataclass
class BenchmarkRunResult:
    benchmark_type: str
    total_problems: int
    passed: int
    pass_at_1: float
    pass_at_1_repair: Optional[float]
    avg_retries: float
    total_cost_usd: float
    total_time_seconds: float
    per_problem_results: list[ProblemResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "benchmark_type": self.benchmark_type,
            "total_problems": self.total_problems,
            "passed": self.passed,
            "pass_at_1": self.pass_at_1,
            "pass_at_1_repair": self.pass_at_1_repair,
            "avg_retries": self.avg_retries,
            "total_cost_usd": self.total_cost_usd,
            "total_time_seconds": self.total_time_seconds,
            "per_problem_results": [
                {
                    "problem_id": r.problem_id,
                    "passed": r.passed,
                    "retries_used": r.retries_used,
                    "cost_usd": r.cost_usd,
                    "time_seconds": r.time_seconds,
                    "error_message": r.error_message,
                }
                for r in self.per_problem_results
            ],
        }


class BenchmarkRunner:
    def __init__(self, settings: Any, benchmark_type: str, with_repair: bool = True) -> None:
        self.settings = settings
        self.benchmark_type = benchmark_type
        self.with_repair = with_repair

    def _load_problems(self) -> list:
        if self.benchmark_type == "humaneval":
            from benchmarks.humaneval.loader import load_problems
            return load_problems()
        elif self.benchmark_type == "mbpp":
            from benchmarks.mbpp.loader import load_problems
            return load_problems()
        elif self.benchmark_type == "custom":
            from benchmarks.custom.evaluator import load_custom_problems
            return load_custom_problems()
        else:
            raise ValueError(f"Unknown benchmark_type: {self.benchmark_type!r}")

    def _problem_to_prompt(self, problem: Any) -> str:
        """Convert a benchmark problem to an orchestrator prompt."""
        bt = self.benchmark_type
        if bt == "humaneval":
            return (
                f"Complete the following Python function:\n\n{problem.prompt}\n\n"
                "Provide only the implementation body."
            )
        elif bt == "mbpp":
            return (
                f"Write a Python function to solve the following task:\n\n"
                f"{problem.text}\n\nEnsure the implementation satisfies these tests:\n"
                + "\n".join(problem.test_list)
            )
        elif bt == "custom":
            return (
                f"Solve the following programming task:\n\n"
                f"{problem['description']}\n\n"
                "The solution must satisfy:\n"
                + "\n".join(problem.get("test_assertions", []))
            )
        return str(problem)

    def _problem_id(self, problem: Any) -> str:
        bt = self.benchmark_type
        if bt == "humaneval":
            return problem.task_id
        elif bt == "mbpp":
            return f"mbpp/{problem.task_id}"
        elif bt == "custom":
            return problem.get("id", "unknown")
        return "unknown"

    async def _evaluate_generated_code(self, problem: Any, generated_code: str, sandbox: Any) -> bool:
        bt = self.benchmark_type
        try:
            if bt == "humaneval":
                from benchmarks.humaneval.evaluator import evaluate_solution
                return await evaluate_solution(problem, generated_code, sandbox)
            elif bt == "mbpp":
                from benchmarks.mbpp.evaluator import evaluate_solution
                return await evaluate_solution(problem, generated_code, sandbox)
            elif bt == "custom":
                from benchmarks.custom.evaluator import evaluate_custom_solution
                return await evaluate_custom_solution(problem, generated_code, sandbox)
        except Exception as exc:
            logger.warning("Evaluation error: %s", exc)
        return False

    async def run_single_problem(self, problem: Any, sandbox: Any) -> ProblemResult:
        """Run orchestrator on a single problem and evaluate the result."""
        from app.agents.orchestrator import Orchestrator

        problem_id = self._problem_id(problem)
        prompt = self._problem_to_prompt(problem)
        task_id = str(uuid.uuid4())

        # Override repair settings if needed
        settings = self.settings
        if not self.with_repair:
            from unittest.mock import MagicMock
            settings = MagicMock(wraps=self.settings)
            settings.max_repair_retries = 0

        start = time.monotonic()
        orchestrator = Orchestrator(settings=settings)
        try:
            result = await orchestrator.run_task(task_id=task_id, prompt=prompt)
            generated_code = result.get("integrated_code", "")
            cost = result.get("total_cost_usd", 0.0)
            retries = result.get("retry_count", 0)
            error = result.get("error_message", "") or ""

            passed = await self._evaluate_generated_code(problem, generated_code, sandbox)
        except Exception as exc:
            logger.error("Orchestrator error on %s: %s", problem_id, exc)
            generated_code = ""
            cost = 0.0
            retries = 0
            error = str(exc)
            passed = False

        elapsed = time.monotonic() - start
        return ProblemResult(
            problem_id=problem_id,
            passed=passed,
            retries_used=retries,
            cost_usd=cost,
            time_seconds=elapsed,
            generated_code=generated_code,
            error_message=error,
        )

    async def run(self) -> BenchmarkRunResult:
        """Load problems, evaluate each, aggregate metrics, save JSON results."""
        from app.config import get_settings
        from app.sandbox.executor import CodeExecutor

        problems = self._load_problems()
        total = len(problems)
        logger.info("Running %s benchmark on %d problems (repair=%s)", self.benchmark_type, total, self.with_repair)

        sandbox = CodeExecutor(self.settings)
        per_problem: list[ProblemResult] = []

        for i, problem in enumerate(problems, 1):
            result = await self.run_single_problem(problem, sandbox)
            per_problem.append(result)
            status = "PASS" if result.passed else "FAIL"
            print(f"Problem {i}/{total}: {result.problem_id} — {status} ({result.time_seconds:.1f}s)")

        passed_count = sum(1 for r in per_problem if r.passed)
        pass_at_1 = passed_count / total if total else 0.0
        avg_retries = sum(r.retries_used for r in per_problem) / total if total else 0.0
        total_cost = sum(r.cost_usd for r in per_problem)
        total_time = sum(r.time_seconds for r in per_problem)

        run_result = BenchmarkRunResult(
            benchmark_type=self.benchmark_type,
            total_problems=total,
            passed=passed_count,
            pass_at_1=pass_at_1,
            pass_at_1_repair=pass_at_1 if self.with_repair else None,
            avg_retries=avg_retries,
            total_cost_usd=total_cost,
            total_time_seconds=total_time,
            per_problem_results=per_problem,
        )

        # Save results
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        out_path = RESULTS_DIR / f"{self.benchmark_type}_{timestamp}.json"
        out_path.write_text(json.dumps(run_result.to_dict(), indent=2))
        logger.info("Results saved to %s", out_path)

        print(f"\n{'='*60}")
        print(f"Benchmark: {self.benchmark_type.upper()}  |  repair={self.with_repair}")
        print(f"pass@1:    {pass_at_1:.3f}  ({passed_count}/{total})")
        print(f"avg retries: {avg_retries:.2f}")
        print(f"total cost:  ${total_cost:.4f}")
        print(f"total time:  {total_time:.1f}s")
        print(f"{'='*60}\n")

        return run_result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m benchmarks.runner",
        description="Run CodeForge benchmarks",
    )
    parser.add_argument(
        "--type",
        choices=["humaneval", "mbpp", "custom", "all"],
        default="humaneval",
        help="Which benchmark to run (default: humaneval)",
    )
    parser.add_argument(
        "--with-repair",
        dest="with_repair",
        action="store_true",
        default=True,
        help="Enable self-repair loop (default: True)",
    )
    parser.add_argument(
        "--no-repair",
        dest="with_repair",
        action="store_false",
        help="Disable self-repair loop",
    )
    parser.add_argument(
        "--output",
        default="benchmarks/results/",
        help="Directory to save results JSON (default: benchmarks/results/)",
    )
    return parser


async def _run_all(settings: Any, with_repair: bool) -> None:
    for bt in ["humaneval", "mbpp", "custom"]:
        runner = BenchmarkRunner(settings=settings, benchmark_type=bt, with_repair=with_repair)
        await runner.run()


def main() -> None:
    import sys
    import os

    # Add codeforge root to path so benchmark imports work
    root = Path(__file__).parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    backend = root / "backend"
    if str(backend) not in sys.path:
        sys.path.insert(0, str(backend))

    parser = _build_parser()
    args = parser.parse_args()

    from app.config import get_settings
    settings = get_settings()

    if args.type == "all":
        asyncio.run(_run_all(settings, args.with_repair))
    else:
        runner = BenchmarkRunner(settings=settings, benchmark_type=args.type, with_repair=args.with_repair)
        asyncio.run(runner.run())


if __name__ == "__main__":
    main()
