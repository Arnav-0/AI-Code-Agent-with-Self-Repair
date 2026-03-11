from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_settings_service
from app.models.schemas import (
    AppSettingsResponse,
    AppSettingsUpdate,
    ConnectionTestRequest,
    ConnectionTestResponse,
)
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/", response_model=AppSettingsResponse)
async def get_settings(
    service: SettingsService = Depends(get_settings_service),
) -> AppSettingsResponse:
    return await service.get_all()


@router.put("/", response_model=AppSettingsResponse)
async def update_settings(
    body: AppSettingsUpdate,
    service: SettingsService = Depends(get_settings_service),
) -> AppSettingsResponse:
    return await service.update(body)


@router.post("/test-connection", response_model=ConnectionTestResponse)
async def test_connection(
    body: ConnectionTestRequest,
    service: SettingsService = Depends(get_settings_service),
) -> ConnectionTestResponse:
    return await service.test_connection(body)
