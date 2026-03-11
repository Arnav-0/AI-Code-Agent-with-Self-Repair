"""Analytics API endpoints for cost and performance data."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_db
from app.models.schemas import CostSummary, ModelDistribution, PerformanceSummary, SelfRepairSummary
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def get_analytics_service(session=Depends(get_db)):
    return AnalyticsService(session)


@router.get("/cost", response_model=CostSummary)
async def get_cost_summary(
    days: int = 30,
    service: AnalyticsService = Depends(get_analytics_service),
) -> CostSummary:
    return await service.get_cost_summary(days=days)


@router.get("/performance", response_model=PerformanceSummary)
async def get_performance_summary(
    days: int = 30,
    service: AnalyticsService = Depends(get_analytics_service),
) -> PerformanceSummary:
    return await service.get_performance_summary(days=days)


@router.get("/self-repair", response_model=SelfRepairSummary)
async def get_self_repair_summary(
    days: int = 30,
    service: AnalyticsService = Depends(get_analytics_service),
) -> SelfRepairSummary:
    return await service.get_self_repair_summary(days=days)


@router.get("/models", response_model=ModelDistribution)
async def get_model_distribution(
    days: int = 30,
    service: AnalyticsService = Depends(get_analytics_service),
) -> ModelDistribution:
    return await service.get_model_distribution(days=days)
