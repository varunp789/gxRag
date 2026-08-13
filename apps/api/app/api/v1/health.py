from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

