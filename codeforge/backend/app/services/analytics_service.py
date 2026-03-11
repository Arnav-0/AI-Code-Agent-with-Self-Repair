"""Analytics service for cost and performance data."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import AgentTrace, Task
from app.models.schemas import (
    ComplexityBreakdown,
    CostSummary,
    DailyCost,
    ErrorPattern,
    ModelDistribution,
    ModelEntry,
    PerformanceSummary,
    SelfRepairSummary,
)


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_cost_summary(self, days: int = 30) -> CostSummary:
        since = datetime.now(tz=timezone.utc) - timedelta(days=days)

        # Total cost and cost by model (from tasks)
        task_result = await self.session.execute(
            select(Task.model_used, func.sum(Task.total_cost_usd))
            .where(Task.created_at >= since)
            .group_by(Task.model_used)
        )
        rows = task_result.all()
        cost_by_model: dict[str, float] = {}
        total_cost = 0.0
        for model, cost in rows:
            c = float(cost or 0.0)
            cost_by_model[model or "unknown"] = c
            total_cost += c

        # Cost by agent type (from traces)
        trace_result = await self.session.execute(
            select(AgentTrace.agent_type, func.sum(AgentTrace.cost_usd))
            .join(Task, AgentTrace.task_id == Task.id)
            .where(Task.created_at >= since)
            .group_by(AgentTrace.agent_type)
        )
        cost_by_agent: dict[str, float] = {
            agent: float(cost or 0.0) for agent, cost in trace_result.all()
        }

        # Daily cost timeseries
        daily_result = await self.session.execute(
            select(
                func.date(Task.created_at).label("day"),
                func.sum(Task.total_cost_usd).label("cost"),
            )
            .where(Task.created_at >= since)
            .group_by(func.date(Task.created_at))
            .order_by(func.date(Task.created_at))
        )
        daily_costs = [
            DailyCost(date=str(day), cost=float(cost or 0.0))
            for day, cost in daily_result.all()
        ]

        return CostSummary(
            total_cost_usd=total_cost,
            cost_by_model=cost_by_model,
            cost_by_agent=cost_by_agent,
            daily_costs=daily_costs,
        )

    async def get_performance_summary(self, days: int = 30) -> PerformanceSummary:
        since = datetime.now(tz=timezone.utc) - timedelta(days=days)

        result = await self.session.execute(
            select(Task).where(Task.created_at >= since)
        )
        tasks = list(result.scalars().all())

        total = len(tasks)
        if total == 0:
            return PerformanceSummary(
                total_tasks=0,
                success_rate=0.0,
                avg_time_ms=0.0,
                avg_retries=0.0,
                tasks_by_status={},
            )

        completed = sum(1 for t in tasks if t.status == "completed")
        success_rate = completed / total if total > 0 else 0.0

        durations = [t.total_time_ms for t in tasks if t.total_time_ms is not None]
        avg_time_ms = sum(durations) / len(durations) if durations else 0.0
        avg_retries = sum(t.retry_count for t in tasks) / total

        tasks_by_status: dict[str, int] = {}
        for t in tasks:
            tasks_by_status[t.status] = tasks_by_status.get(t.status, 0) + 1

        return PerformanceSummary(
            total_tasks=total,
            success_rate=success_rate,
            avg_time_ms=avg_time_ms,
            avg_retries=avg_retries,
            tasks_by_status=tasks_by_status,
        )

    async def get_self_repair_summary(self, days: int = 30) -> SelfRepairSummary:
        since = datetime.now(tz=timezone.utc) - timedelta(days=days)

        result = await self.session.execute(
            select(Task).where(Task.created_at >= since)
        )
        tasks = list(result.scalars().all())

        total = len(tasks)
        if total == 0:
            return SelfRepairSummary(
                total_tasks=0,
                tasks_with_retries=0,
                repair_success_rate=0.0,
                first_try_success_rate=0.0,
                avg_retries_when_repairing=0.0,
                max_retries_seen=0,
                total_repair_cost_usd=0.0,
                complexity_breakdown=[],
                error_patterns=[],
                daily_repair_rate=[],
            )

        completed = [t for t in tasks if t.status == "completed"]
        with_retries = [t for t in tasks if t.retry_count > 0]
        repaired_and_completed = [t for t in completed if t.retry_count > 0]
        first_try = [t for t in completed if t.retry_count == 0]

        repair_success_rate = (
            len(repaired_and_completed) / len(with_retries)
            if with_retries
            else 0.0
        )
        first_try_success_rate = len(first_try) / total if total else 0.0
        avg_retries_repairing = (
            sum(t.retry_count for t in with_retries) / len(with_retries)
            if with_retries
            else 0.0
        )
        max_retries = max((t.retry_count for t in tasks), default=0)

        # Estimate repair cost: cost of tasks with retries minus avg first-try cost
        avg_first_try_cost = (
            sum(float(t.total_cost_usd) for t in first_try) / len(first_try)
            if first_try
            else 0.0
        )
        total_repair_cost = sum(
            max(float(t.total_cost_usd) - avg_first_try_cost, 0.0)
            for t in with_retries
        )

        # Complexity breakdown
        by_complexity: dict[str, list[Task]] = {}
        for t in tasks:
            c = t.complexity or "unknown"
            by_complexity.setdefault(c, []).append(t)

        complexity_breakdown = []
        for comp, ctasks in sorted(by_complexity.items()):
            c_completed = [t for t in ctasks if t.status == "completed"]
            c_repaired = [t for t in c_completed if t.retry_count > 0]
            c_failed = [t for t in ctasks if t.status == "failed"]
            complexity_breakdown.append(
                ComplexityBreakdown(
                    complexity=comp,
                    total=len(ctasks),
                    succeeded=len(c_completed),
                    repaired=len(c_repaired),
                    failed=len(c_failed),
                    avg_retries=round(
                        sum(t.retry_count for t in ctasks) / len(ctasks), 2
                    ),
                    avg_cost_usd=round(
                        sum(float(t.total_cost_usd) for t in ctasks) / len(ctasks), 6
                    ),
                )
            )

        # Error patterns from failed tasks and tasks with retries
        error_counts: dict[str, dict] = {}
        for t in tasks:
            if t.error_message and t.retry_count > 0:
                # Extract error class from message
                err_type = t.error_message.split(":")[0].split("(")[0].strip()
                if len(err_type) > 60:
                    err_type = err_type[:57] + "..."
                if err_type not in error_counts:
                    error_counts[err_type] = {"count": 0, "fixed": 0}
                error_counts[err_type]["count"] += 1
                if t.status == "completed":
                    error_counts[err_type]["fixed"] += 1
            elif t.retry_count > 0 and t.status == "completed":
                err_type = "Runtime Error (auto-fixed)"
                if err_type not in error_counts:
                    error_counts[err_type] = {"count": 0, "fixed": 0}
                error_counts[err_type]["count"] += 1
                error_counts[err_type]["fixed"] += 1

        error_patterns = [
            ErrorPattern(
                error_type=etype,
                count=data["count"],
                repair_success_rate=round(
                    data["fixed"] / data["count"] if data["count"] > 0 else 0.0, 3
                ),
            )
            for etype, data in sorted(
                error_counts.items(), key=lambda x: x[1]["count"], reverse=True
            )[:10]
        ]

        # Daily repair rate
        daily_data: dict[str, dict] = {}
        for t in tasks:
            day = str(t.created_at.date()) if t.created_at else "unknown"
            if day not in daily_data:
                daily_data[day] = {"total": 0, "repaired": 0}
            daily_data[day]["total"] += 1
            if t.retry_count > 0:
                daily_data[day]["repaired"] += 1

        daily_repair_rate = [
            DailyCost(
                date=day,
                cost=round(d["repaired"] / d["total"] * 100, 1) if d["total"] > 0 else 0.0,
            )
            for day, d in sorted(daily_data.items())
        ]

        return SelfRepairSummary(
            total_tasks=total,
            tasks_with_retries=len(with_retries),
            repair_success_rate=round(repair_success_rate, 3),
            first_try_success_rate=round(first_try_success_rate, 3),
            avg_retries_when_repairing=round(avg_retries_repairing, 2),
            max_retries_seen=max_retries,
            total_repair_cost_usd=round(total_repair_cost, 6),
            complexity_breakdown=complexity_breakdown,
            error_patterns=error_patterns,
            daily_repair_rate=daily_repair_rate,
        )

    async def get_model_distribution(self, days: int = 30) -> ModelDistribution:
        since = datetime.now(tz=timezone.utc) - timedelta(days=days)

        result = await self.session.execute(
            select(Task.model_used, func.count(Task.id).label("cnt"))
            .where(Task.created_at >= since)
            .group_by(Task.model_used)
            .order_by(func.count(Task.id).desc())
        )
        rows = result.all()

        total = sum(cnt for _, cnt in rows)
        distribution = [
            ModelEntry(
                model=model or "unknown",
                count=cnt,
                percentage=round(cnt / total * 100, 2) if total > 0 else 0.0,
            )
            for model, cnt in rows
        ]

        return ModelDistribution(distribution=distribution)
