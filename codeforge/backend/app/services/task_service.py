from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import AgentTrace, Task
from app.models.schemas import HistoryFilter, PaginationParams


class TaskService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_task(self, prompt: str) -> Task:
        task = Task(prompt=prompt, status="pending")
        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def get_task(self, task_id: uuid.UUID) -> Optional[Task]:
        result = await self.session.execute(
            select(Task)
            .options(selectinload(Task.traces))
            .where(Task.id == task_id)
        )
        return result.scalar_one_or_none()

    async def get_task_traces(self, task_id: uuid.UUID) -> list[AgentTrace]:
        result = await self.session.execute(
            select(AgentTrace)
            .where(AgentTrace.task_id == task_id)
            .order_by(AgentTrace.step_order)
        )
        return list(result.scalars().all())

    async def delete_task(self, task_id: uuid.UUID) -> bool:
        task = await self.session.get(Task, task_id)
        if task is None:
            return False
        await self.session.delete(task)
        await self.session.flush()
        return True

    async def list_tasks(
        self,
        filters: HistoryFilter,
        pagination: PaginationParams,
    ) -> tuple[list[Task], int]:
        query = select(Task)
        count_query = select(func.count()).select_from(Task)

        if filters.status:
            query = query.where(Task.status == filters.status)
            count_query = count_query.where(Task.status == filters.status)

        if filters.search:
            like_expr = f"%{filters.search}%"
            query = query.where(Task.prompt.ilike(like_expr))
            count_query = count_query.where(Task.prompt.ilike(like_expr))

        if filters.date_from:
            query = query.where(Task.created_at >= filters.date_from)
            count_query = count_query.where(Task.created_at >= filters.date_from)

        if filters.date_to:
            query = query.where(Task.created_at <= filters.date_to)
            count_query = count_query.where(Task.created_at <= filters.date_to)

        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        sort_col = getattr(Task, filters.sort_by, Task.created_at)
        if filters.order == "desc":
            query = query.order_by(desc(sort_col))
        else:
            query = query.order_by(asc(sort_col))

        offset = (pagination.page - 1) * pagination.per_page
        query = query.offset(offset).limit(pagination.per_page)

        result = await self.session.execute(query)
        tasks = list(result.scalars().all())

        return tasks, total
