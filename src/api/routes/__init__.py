from fastapi import APIRouter

from .events import router as events_router
from .health import router as health_router
from .sync import router as sync_router

router = APIRouter()

router.include_router(health_router)
router.include_router(sync_router)
router.include_router(events_router)
