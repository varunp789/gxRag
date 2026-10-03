from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from app.db import store as db_store
from typing import Annotated
from app.dependencies.access import require_admin
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
def operational_health(_: Annotated[AdminUser, Depends(require_admin("admin.support"))]) -> dict[str, object]:
    return {"status":"ok", "queue":backlog(), "artifact_integrity":artifact_integrity()}


@router.get("/ready")
def readiness() -> JSONResponse:
    """Dependency readiness for orchestrator probes (503 when degraded)."""
    checks: dict[str, str] = {}
    if db_store.enabled():
        try:
            with db_store.connection() as conn, conn.cursor() as cursor:
                cursor.execute("SELECT 1")
            checks["database"] = "ok"
        except Exception as error:  # noqa: BLE001 - report any connectivity failure
            checks["database"] = f"error: {type(error).__name__}"
    try:
        backlog()
        checks["queue"] = "ok"
    except Exception as error:  # noqa: BLE001
        checks["queue"] = f"error: {type(error).__name__}"
    healthy = all(value == "ok" for value in checks.values())
    return JSONResponse(status_code=200 if healthy else 503,
                        content={"status": "ready" if healthy else "degraded", "checks": checks})
