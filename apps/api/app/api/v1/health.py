from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from typing import Annotated
from app.dependencies.access import get_current_admin
from app.models.access import AdminUser
from app.services.job_queue import backlog
from app.services.observability import artifact_integrity

router = APIRouter()


@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@router.get("/admin/health", tags=["admin"])
def operational_health(_: Annotated[AdminUser, Depends(get_current_admin)]) -> dict[str, object]:
    return {"status":"ok", "queue":backlog(), "artifact_integrity":artifact_integrity()}
