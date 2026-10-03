"""Retention: permanently purge assets whose deletion grace period has elapsed.

Deleting an asset through the API soft-deletes it (content stops being served,
source bytes are redacted).  This job removes everything that remains: derived
artifacts on disk, index entries in every backend, and the registry rows.
"""

from __future__ import annotations

import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.core.config import settings
from app.db import store as db_store
from app.services import asset_registry as registry
from app.services.governance import audit
from app.services.index_backends import delete_asset_everywhere
from app.services.observability import emit


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def purge_due_assets(now: datetime | None = None, retention_days: int | None = None) -> dict[str, list[str]]:
    """Purge soft-deleted assets older than the retention window.

    Returns {"purged": [...], "failed": [...]}; failures are retried next run.
    """
    registry.seed_assets()
    now = now or datetime.now(timezone.utc)
    days = settings.retention_days if retention_days is None else retention_days
    cutoff = now - timedelta(days=days)
    purged: list[str] = []
    failed: list[str] = []
    for asset in [a for a in registry.ASSETS if a.status == "deleted" and _parse(a.updated_at) <= cutoff]:
        try:
            delete_asset_everywhere(workspace_id=asset.workspace_id, asset_id=asset.id)
            shutil.rmtree(Path(settings.artifact_root) / asset.workspace_id / asset.id, ignore_errors=False)
        except FileNotFoundError:
            pass
        except Exception as error:  # noqa: BLE001 - keep the asset so the next run retries
            emit("retention.purge_failed", asset_id=asset.id, error=str(error))
            failed.append(asset.id)
            continue
        _remove_rows(asset.id)
        audit("system:retention", "asset.purged", "asset", asset.id, asset.workspace_id)
        purged.append(asset.id)
    return {"purged": purged, "failed": failed}


def _remove_rows(asset_id: str) -> None:
    if db_store.enabled():
        with db_store.connection() as conn, conn.cursor() as cursor:
            cursor.execute("DELETE FROM assets WHERE id = %s", (asset_id,))  # cascades to dependants
            conn.commit()
    registry.ASSETS[:] = [x for x in registry.ASSETS if x.id != asset_id]
    registry.ASSET_SOURCES[:] = [x for x in registry.ASSET_SOURCES if x.asset_id != asset_id]
    registry.ASSET_UPLOADS[:] = [x for x in registry.ASSET_UPLOADS if x.asset_id != asset_id]
    registry.ASSET_VERSIONS[:] = [x for x in registry.ASSET_VERSIONS if x.asset_id != asset_id]
    registry.ARTIFACTS[:] = [x for x in registry.ARTIFACTS if x.asset_id != asset_id]
    registry.PROCESSING_JOBS[:] = [x for x in registry.PROCESSING_JOBS if x.asset_id != asset_id]
    registry.INDEX_RECORDS[:] = [x for x in registry.INDEX_RECORDS if x.asset_id != asset_id]
    if not db_store.enabled():
        registry._persist_state()


if __name__ == "__main__":
    print(purge_due_assets())
