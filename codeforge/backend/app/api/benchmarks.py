from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_benchmark_service
from app.models.schemas import BenchmarkRunDetail, BenchmarkRunRequest, BenchmarkRunResponse
from app.services.benchmark_service import BenchmarkService

router = APIRouter(prefix="/benchmarks", tags=["Benchmarks"])


@router.post("/run", response_model=BenchmarkRunResponse, status_code=202)
async def trigger_benchmark(
    body: BenchmarkRunRequest,
    service: BenchmarkService = Depends(get_benchmark_service),
) -> BenchmarkRunResponse:
    run = await service.trigger_run(body)
    return BenchmarkRunResponse.model_validate(run)


@router.get("/runs", response_model=list[BenchmarkRunResponse])
async def list_runs(
    service: BenchmarkService = Depends(get_benchmark_service),
) -> list[BenchmarkRunResponse]:
    runs = await service.list_runs()
    return [BenchmarkRunResponse.model_validate(r) for r in runs]


@router.get("/runs/{run_id}", response_model=BenchmarkRunDetail)
async def get_run(
    run_id: uuid.UUID,
    service: BenchmarkService = Depends(get_benchmark_service),
) -> BenchmarkRunDetail:
    run = await service.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Benchmark run not found")
    return BenchmarkRunDetail.model_validate(run)
