from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import BenchmarkRun
from app.models.schemas import BenchmarkRunRequest


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
        )
        self.session.add(run)
        await self.session.flush()
        await self.session.refresh(run)
        return run
