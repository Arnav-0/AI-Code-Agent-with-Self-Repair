from __future__ import annotations

import math
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_task_service
from app.models.schemas import (
    HistoryFilter,
    PaginationParams,
    TaskListResponse,
    TaskResponse,
)
from app.services.task_service import TaskService

router = APIRouter(prefix="/history", tags=["History"])


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    sort_by: str = Query("created_at"),
    order: str = Query("desc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    service: TaskService = Depends(get_task_service),
) -> TaskListResponse:
    filters = HistoryFilter(
        status=status,
        search=search,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        order=order,  # type: ignore[arg-type]
    )
    pagination = PaginationParams(page=page, per_page=per_page)

    tasks, total = await service.list_tasks(filters, pagination)
    total_pages = math.ceil(total / per_page) if total > 0 else 1

    return TaskListResponse(
        items=[TaskResponse.model_validate(t) for t in tasks],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )
