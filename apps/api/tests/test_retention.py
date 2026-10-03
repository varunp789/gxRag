from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.core.config import settings
from app.services import asset_registry, retention
from tests.conftest import ingest, owner

PAGE = "<p>Orbit Bio Labs develops Zarnotide for the Kelvar pathway.</p>"


def _artifact_dir(asset_id):
    return Path(settings.artifact_root) / "ws_orbit_prod" / asset_id


def test_nothing_is_purged_inside_the_retention_window(client):
    asset_id, _ = ingest(client, owner(), title="Launch", text=PAGE)
    client.delete(f"/v1/assets/{asset_id}", headers=owner())
    assert retention.purge_due_assets() == {"purged": [], "failed": []}
    assert _artifact_dir(asset_id).exists()
    assert asset_registry._find_asset(asset_id) is not None


def test_live_assets_are_never_purged(client):
    asset_id, _ = ingest(client, owner(), title="Launch", text=PAGE)
    future = datetime.now(timezone.utc) + timedelta(days=3650)
    assert retention.purge_due_assets(now=future)["purged"] == []
    assert _artifact_dir(asset_id).exists()


def test_purge_removes_files_rows_and_records_audit(client):
    asset_id, _ = ingest(client, owner(), title="Launch", text=PAGE)
    client.delete(f"/v1/assets/{asset_id}", headers=owner())
    later = datetime.now(timezone.utc) + timedelta(days=settings.retention_days + 1)
    assert retention.purge_due_assets(now=later) == {"purged": [asset_id], "failed": []}
    assert not _artifact_dir(asset_id).exists()
    asset_registry.reset_state()
    asset_registry.seed_assets()
    assert asset_registry._find_asset(asset_id) is None
    assert not [a for a in asset_registry.ARTIFACTS if a.asset_id == asset_id]
    assert client.get(f"/v1/assets/{asset_id}", headers=owner()).status_code == 404
    assert "asset.purged" in {r["action"] for r in client.get("/v1/audit-logs", headers=owner()).json()}


def test_backend_failure_keeps_the_asset_for_retry(client, monkeypatch):
    asset_id, _ = ingest(client, owner(), title="Launch", text=PAGE)
    client.delete(f"/v1/assets/{asset_id}", headers=owner())
    later = datetime.now(timezone.utc) + timedelta(days=31)

    def boom(**kwargs):
        raise RuntimeError("opensearch down")

    monkeypatch.setattr(retention, "delete_asset_everywhere", boom)
    assert retention.purge_due_assets(now=later) == {"purged": [], "failed": [asset_id]}
    assert _artifact_dir(asset_id).exists() and asset_registry._find_asset(asset_id) is not None
    monkeypatch.setattr(retention, "delete_asset_everywhere", lambda **kw: None)
    assert retention.purge_due_assets(now=later)["purged"] == [asset_id]


def test_admin_endpoint_requires_operate_permission(client, monkeypatch):
    from app.models.access import AdminUser
    from app.services import catalog

    assert client.post("/v1/admin/retention/run").status_code == 200
    monkeypatch.setattr(catalog, "ADMIN_USERS", [*catalog.ADMIN_USERS,
                        AdminUser(id="a2", email="support@gxrag.dev", full_name="S", roles=["support_admin"])])
    assert client.post("/v1/admin/retention/run", headers={"X-Admin-Email": "support@gxrag.dev"}).status_code == 403
