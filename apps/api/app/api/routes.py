from fastapi import APIRouter

from app.api.v1.access import router as access_router
from app.api.v1.assets import router as assets_router
from app.api.v1.health import router as health_router
from app.api.v1.platform import router as platform_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(platform_router, tags=["platform"])
api_router.include_router(access_router)
api_router.include_router(assets_router)
