from fastapi import APIRouter

from app.api.analytics import router as analytics_router
from app.api.benchmarks import router as benchmarks_router
from app.api.conversations import router as conversations_router
from app.api.health import router as health_router
from app.api.history import router as history_router
from app.api.settings import router as settings_router
from app.api.tasks import router as tasks_router
from app.api.websocket import router as websocket_router

router = APIRouter()

router.include_router(health_router)
router.include_router(tasks_router)
router.include_router(history_router)
router.include_router(benchmarks_router)
router.include_router(settings_router)
router.include_router(analytics_router)
router.include_router(websocket_router)
router.include_router(conversations_router)
