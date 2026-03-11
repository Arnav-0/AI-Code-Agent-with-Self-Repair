from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import BenchmarkRun, BenchmarkResult
from app.models.schemas import BenchmarkRunRequest

logger = logging.getLogger(__name__)


class BenchmarkService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_runs(self) -> list[BenchmarkRun]:
        result = await self.session.execute(
            select(BenchmarkRun).order_by(BenchmarkRun.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_run(self, run_id: uuid.UUID) -> Optional[BenchmarkRun]:
        result = await self.session.execute(
            select(BenchmarkRun)
            .options(selectinload(BenchmarkRun.results))
            .where(BenchmarkRun.id == run_id)
        )
        return result.scalar_one_or_none()

    async def trigger_run(self, request: BenchmarkRunRequest) -> BenchmarkRun:
        run = BenchmarkRun(
            benchmark_type=request.type,
            model_config_json={"with_repair": request.with_repair},
            total_problems=0,
            passed=0,
            pass_at_1=0.0,
            status="running",
        )
        self.session.add(run)
        await self.session.flush()
        await self.session.refresh(run)

        # Launch benchmark execution in background
        run_id = run.id
        asyncio.create_task(
            self._execute_benchmark(run_id, request.type, request.with_repair)
        )

        return run

    async def _execute_benchmark(
        self, run_id: uuid.UUID, benchmark_type: str, with_repair: bool
    ) -> None:
        """Execute the benchmark in the background and update the DB record."""
        from app.config import get_settings
        from app.db.session import async_session_factory

        settings = get_settings()

        try:
            from benchmarks.runner import BenchmarkRunner

            runner = BenchmarkRunner(
                settings=settings,
                benchmark_type=benchmark_type,
                with_repair=with_repair,
            )
            result = await runner.run()

            async with async_session_factory() as session:
                db_run = await session.get(BenchmarkRun, run_id)
                if db_run:
                    db_run.total_problems = result.total_problems
                    db_run.passed = result.passed
                    db_run.pass_at_1 = result.pass_at_1
                    db_run.status = "completed"

                    for pr in result.per_problem_results:
                        br = BenchmarkResult(
                            run_id=run_id,
                            problem_id=pr.problem_id,
                            passed=pr.passed,
                            retries_used=pr.retries_used,
                            generated_code=pr.generated_code,
                            error_message=pr.error_message or None,
                            cost_usd=pr.cost_usd,
                            time_ms=int(pr.time_seconds * 1000),
                        )
                        session.add(br)

                    await session.commit()
                    logger.info(
                        "Benchmark %s completed: %d/%d passed (%.1f%%)",
                        run_id, result.passed, result.total_problems,
                        result.pass_at_1 * 100,
                    )
        except Exception as exc:
            logger.error("Benchmark %s failed: %s", run_id, exc)
            try:
                async with async_session_factory() as session:
                    db_run = await session.get(BenchmarkRun, run_id)
                    if db_run:
                        db_run.status = "failed"
                    await session.commit()
            except Exception:
                pass
