"""Integration tests against a real PostgreSQL server.

Set GXRAG_TEST_DATABASE_URL to a server URL with CREATE DATABASE rights, e.g.
postgresql://postgres@localhost:5432/postgres. Each test run uses a throwaway database.
"""

import os
import uuid

import psycopg
import pytest
from psycopg.conninfo import make_conninfo

from app.core.config import settings
from app.db import migrate as migrations
from app.db import store
from tests.conftest import b64, ingest, owner, rivet

ADMIN_URL = os.environ.get("GXRAG_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not ADMIN_URL, reason="GXRAG_TEST_DATABASE_URL not set")

PAGE = "<p>Orbit Bio Labs develops Zarnotide. Zarnotide inhibits the Kelvar pathway.</p>"


@pytest.fixture
def database(monkeypatch):
    name = f"gxrag_t_{uuid.uuid4().hex[:10]}"
    with psycopg.connect(ADMIN_URL, autocommit=True) as admin:
        admin.execute(f'CREATE DATABASE "{name}"')
    url = make_conninfo(ADMIN_URL, dbname=name)
    migrations.migrate(url)
    migrations.seed_catalog(url)
    monkeypatch.setattr(settings, "database_url", url)
    from app.services import asset_registry
    asset_registry.reset_state()
    store._loaded_hashes.clear()
    yield url
    asset_registry.reset_state()
    with psycopg.connect(ADMIN_URL, autocommit=True) as admin:
        admin.execute(f'DROP DATABASE "{name}" WITH (FORCE)')


def _scalar(url, sql, *params):
    with psycopg.connect(url) as conn:
        return conn.execute(sql, params).fetchone()[0]


def test_migrations_are_idempotent_and_complete(database):
    assert migrations.migrate(database) == []
    tables = {r[0] for r in psycopg.connect(database).execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'").fetchall()}
    assert {"tenants", "workspaces", "users", "workspace_members", "api_keys", "assets", "processing_jobs",
            "artifacts", "index_records", "usage_counters", "audit_logs", "schema_migrations"} <= tables
    assert _scalar(database, "SELECT count(*) FROM schema_migrations") == 4
    assert _scalar(database, "SELECT count(*) FROM workspaces") == 3


def test_foreign_keys_block_orphans(database):
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        with psycopg.connect(database) as conn:
            conn.execute("INSERT INTO assets (id, workspace_id, tenant_id, status, data) "
                         "VALUES ('a','ws_nope','tenant_orbit','x','{}')")


def test_audit_log_is_append_only(database):
    store.insert_audit("alex", "x.y", "asset", "a1", "ws_orbit_prod")
    for sql in ("UPDATE audit_logs SET action = 'tampered'", "DELETE FROM audit_logs"):
        with pytest.raises(psycopg.errors.RaiseException):
            with psycopg.connect(database) as conn:
                conn.execute(sql)
    assert _scalar(database, "SELECT action FROM audit_logs") == "x.y"


def test_state_survives_process_restart(client, database):
    from app.services import asset_registry
    asset_id, status = ingest(client, owner(), title="Launch", text=PAGE)
    assert status["asset_status"] == "ready"
    asset_registry.reset_state()  # simulate a fresh API process
    again = client.get(f"/v1/assets/{asset_id}/status", headers=owner()).json()
    assert again["asset_status"] == "ready" and len(again["artifacts"]) == 9
    assert _scalar(database, "SELECT count(*) FROM artifacts WHERE asset_id = %s", asset_id) == 9
    body = client.post("/v1/query/hybrid", json={"query": "Zarnotide Kelvar"}, headers=owner()).json()
    assert body["results"]


def test_worker_sees_assets_created_by_api_after_it_started(client, database):
    from worker.main import run_once

    from app.services import asset_registry

    asset_registry.seed_assets()  # worker boots and caches state first
    body = {"title": "Late", "asset_type": "web_page", "file_name": "a.html", "mime_type": "text/html",
            "size_bytes": 1, "content_base64": b64(PAGE)}
    asset_id = client.post("/v1/assets/upload", json=body, headers=owner()).json()["asset"]["id"]
    client.post(f"/v1/assets/{asset_id}/process", json={"content_base64": b64(PAGE)}, headers=owner())
    assert run_once() is True
    assert client.get(f"/v1/assets/{asset_id}/status", headers=owner()).json()["asset_status"] == "ready"


def test_stale_process_does_not_overwrite_newer_rows(database):
    from app.services import asset_registry
    asset_registry.seed_assets()
    snapshot = asset_registry._snapshot()  # a process holding old state
    with psycopg.connect(database) as conn:  # another process updates the asset
        conn.execute("UPDATE assets SET data = jsonb_set(data, '{title}', '\"Changed elsewhere\"') "
                     "WHERE id = 'asset_orbit_trial_pdf'")
    assert store.save_all(snapshot) == 0  # unchanged rows are not rewritten
    title = _scalar(database, "SELECT data->>'title' FROM assets WHERE id = 'asset_orbit_trial_pdf'")
    assert title == "Changed elsewhere"


def test_usage_counters_persist_and_are_monthly(client, database, monkeypatch):
    client.post("/v1/query/vector", json={"query": "x"}, headers=owner())
    client.post("/v1/query/vector", json={"query": "x"}, headers=owner())
    assert client.get("/v1/usage", headers=owner()).json()["usage"]["query"] == 2
    assert client.get("/v1/usage", headers=rivet()).json()["usage"] == {}
    monkeypatch.setattr(store, "current_period", lambda now=None: "2099-01")
    assert client.get("/v1/usage", headers=owner()).json()["usage"] == {}


def test_audit_records_actor_and_scope(client, database):
    ingest(client, owner(), title="Launch", text=PAGE)
    rows = client.get("/v1/audit-logs", headers=owner()).json()
    assert rows[0]["actor"] == "alex@orbit.bio" and rows[0]["workspace_id"] == "ws_orbit_prod"
    assert client.get("/v1/audit-logs", headers={**owner("ws_orbit_research")}).json() == []
    assert any(r["action"] == "asset.uploaded" for r in client.get("/v1/admin/audit-logs").json())


def test_api_keys_are_hashed_in_the_database(client, database, monkeypatch):
    created = client.post("/v1/api-keys", json={"name": "ci", "role": "retrieval_reader"}, headers=owner()).json()
    stored = _scalar(database, "SELECT key_hash FROM api_keys WHERE id = %s", created["key"]["id"])
    assert stored and stored not in created["secret"] and created["secret"].split("_", 2)[2] not in stored
    monkeypatch.setattr(settings, "auth_mode", "jwt")
    headers = {"Authorization": f"Bearer {created['secret']}"}
    assert client.get("/v1/assets", headers=headers).status_code == 200
    monkeypatch.setattr(settings, "auth_mode", "dev")
    client.delete(f"/v1/api-keys/{created['key']['id']}", headers=owner())
    monkeypatch.setattr(settings, "auth_mode", "jwt")
    assert client.get("/v1/assets", headers=headers).status_code == 401


def test_readiness_reflects_database_health(client, database, monkeypatch):
    assert client.get("/v1/ready").json()["checks"]["database"] == "ok"
    monkeypatch.setattr(settings, "database_url", "postgresql://nobody@127.0.0.1:1/none")
    response = client.get("/v1/ready")
    assert response.status_code == 503 and response.json()["status"] == "degraded"


def test_deletion_persists(client, database):
    asset_id, _ = ingest(client, owner(), title="Launch", text=PAGE)
    assert client.delete(f"/v1/assets/{asset_id}", headers=owner()).status_code == 204
    assert _scalar(database, "SELECT status FROM assets WHERE id = %s", asset_id) == "deleted"
    assert _scalar(database, "SELECT data->>'location' FROM asset_sources WHERE asset_id = %s", asset_id) == "deleted://redacted"


def test_purge_cascades_through_the_database_and_clears_index_tables(client, database, monkeypatch):
    from datetime import datetime, timedelta, timezone

    from app.services import index_backends, retention

    with psycopg.connect(database) as conn:  # the tables the index writers would create
        conn.execute("CREATE TABLE IF NOT EXISTS gxrag_vectors (workspace_id text, asset_id text, chunk_id text, content text)")
        conn.execute("CREATE TABLE IF NOT EXISTS gxrag_structured_rows (workspace_id text, asset_id text, row_number int, data jsonb)")
    asset_id, _ = ingest(client, owner(), title="Launch", text=PAGE)
    with psycopg.connect(database) as conn:
        for table, extra in (("gxrag_vectors", "'0','x'"), ("gxrag_structured_rows", "0,'{}'")):
            conn.execute(f"INSERT INTO {table} VALUES ('ws_orbit_prod','{asset_id}',{extra})")
            conn.execute(f"INSERT INTO {table} VALUES ('ws_orbit_prod','asset_keep',{extra})")

    class Reply:
        status_code = 404

    monkeypatch.setattr(index_backends.httpx, "post", lambda *a, **k: Reply())
    monkeypatch.setattr(index_backends, "_arango_request", lambda *a, **k: Reply())
    monkeypatch.setattr(settings, "vector_database_url", database)
    monkeypatch.setattr(retention, "delete_asset_everywhere", index_backends.delete_asset_everywhere)

    client.delete(f"/v1/assets/{asset_id}", headers=owner())
    later = datetime.now(timezone.utc) + timedelta(days=settings.retention_days + 1)
    assert retention.purge_due_assets(now=later)["purged"] == [asset_id]

    for table in ("assets", "asset_sources", "asset_versions", "processing_jobs", "artifacts", "index_records"):
        column = "id" if table == "assets" else "asset_id"
        assert _scalar(database, f"SELECT count(*) FROM {table} WHERE {column} = %s", asset_id) == 0, table
    for table in ("gxrag_vectors", "gxrag_structured_rows"):
        assert _scalar(database, f"SELECT count(*) FROM {table} WHERE asset_id = %s", asset_id) == 0
        assert _scalar(database, f"SELECT count(*) FROM {table} WHERE asset_id = 'asset_keep'") == 1
    assert _scalar(database, "SELECT count(*) FROM audit_logs WHERE action = 'asset.purged'") == 1


def test_billing_mapping_and_webhook_dedup_persist(client, database):
    from app.core.security import issue_token  # noqa: F401
    from app.services import billing
    from app.services.governance import sign_webhook

    assert client.put("/v1/admin/tenants/tenant_orbit/billing-customer", json={"customer_id": "cus_db1"}).status_code == 204
    assert _scalar(database, "SELECT stripe_customer_id FROM tenants WHERE id = 'tenant_orbit'") == "cus_db1"
    assert client.put("/v1/admin/tenants/tenant_rivet/billing-customer", json={"customer_id": "cus_db1"}).status_code == 409
    body = b'{"id":"evt_db","type":"invoice.paid","data":{"object":{"customer":"cus_db1"}}}'
    send = lambda: client.post("/v1/webhooks/stripe", content=body, headers={"Stripe-Signature": sign_webhook(body, settings.stripe_webhook_secret)})  # noqa: E731
    assert send().json()["duplicate"] is False
    billing.reset()  # in-memory state is irrelevant: dedup must come from the database
    assert send().json()["duplicate"] is True
    assert _scalar(database, "SELECT count(*) FROM webhook_events") == 1
