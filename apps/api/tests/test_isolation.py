"""Tenant / workspace isolation across assets, queries, exports, deletes and admin views."""

from tests.conftest import analyst, ingest, owner, rivet

ORBIT_TEXT = "Orbit Bio Labs studies Zarnotide. Zarnotide inhibits the Kelvar pathway in mice."
RIVET_TEXT = "Rivet Capital holds Quantrix bonds. Quantrix matures in 2031."


def _seed_two_tenants(client):
    orbit_id, _ = ingest(client, owner(), title="Orbit note", text=ORBIT_TEXT)
    rivet_id, _ = ingest(client, rivet(), title="Rivet note", text=RIVET_TEXT)
    return orbit_id, rivet_id


def test_cross_tenant_asset_access_is_404(client):
    orbit_id, rivet_id = _seed_two_tenants(client)
    for suffix in ("", "/status", "/graph", "/entities", "/relations", "/export"):
        assert client.get(f"/v1/assets/{orbit_id}{suffix}", headers=rivet()).status_code == 404, suffix
        assert client.get(f"/v1/assets/{rivet_id}{suffix}", headers=owner()).status_code == 404, suffix
    assert client.post(f"/v1/assets/{orbit_id}/process", json={}, headers=rivet()).status_code == 404
    assert client.delete(f"/v1/assets/{orbit_id}", headers=rivet()).status_code == 404
    assert client.get(f"/v1/assets/{orbit_id}", headers=owner()).status_code == 200  # untouched


def test_asset_lists_are_scoped(client):
    orbit_id, rivet_id = _seed_two_tenants(client)
    orbit = {a["asset"]["id"] for a in client.get("/v1/assets", headers=owner()).json()}
    other = {a["asset"]["id"] for a in client.get("/v1/assets", headers=rivet()).json()}
    assert orbit_id in orbit and rivet_id not in orbit
    assert other == {rivet_id}


def test_cannot_select_a_workspace_you_do_not_belong_to(client):
    assert client.get("/v1/assets", headers={**rivet(), "X-Workspace-Id": "ws_orbit_prod"}).status_code == 403
    assert client.get("/v1/assets", headers={**analyst(), "X-Workspace-Id": "ws_orbit_research"}).status_code == 403
    assert client.get("/v1/assets", headers={**owner(), "X-Workspace-Id": "ws_does_not_exist"}).status_code == 403


def test_queries_never_return_other_tenants_content(client):
    _seed_two_tenants(client)
    for mode in ("vector", "hybrid", "graph", "multimodal", "structured"):
        body = client.post(f"/v1/query/{mode}", json={"query": "Quantrix bonds"}, headers=owner()).json()
        assert "Quantrix" not in str(body["results"]) + str(body["citations"]), mode
        body = client.post(f"/v1/query/{mode}", json={"query": "Zarnotide Kelvar"}, headers=rivet()).json()
        assert "Zarnotide" not in str(body["results"]) + str(body["citations"]), mode
    own = client.post("/v1/query/hybrid", json={"query": "Zarnotide Kelvar"}, headers=owner()).json()
    assert "Zarnotide" in str(own)


def test_query_filter_by_foreign_asset_id_returns_nothing(client):
    orbit_id, _ = _seed_two_tenants(client)
    body = client.post("/v1/query/hybrid", json={"query": "Zarnotide", "asset_id": orbit_id}, headers=rivet()).json()
    assert body["results"] == []


def test_hosted_answers_do_not_leak_context(client):
    _seed_two_tenants(client)
    body = client.post("/v1/answers/hybrid", json={"query": "Quantrix"}, headers=owner()).json()
    assert body["citations"] == []


def test_admin_endpoints_reject_workspace_users_in_jwt_mode(client, jwt_mode):
    from tests.conftest import bearer
    for path in ("/v1/admin/assets", "/v1/admin/jobs", "/v1/admin/usage", "/v1/admin/audit-logs",
                 "/v1/admin/query-logs", "/v1/admin/health", "/v1/access/overview"):
        assert client.get(path, headers=bearer("alex@orbit.bio")).status_code == 403, path


def test_workspace_audit_log_is_scoped(client):
    orbit_id, rivet_id = _seed_two_tenants(client)
    rows = client.get("/v1/audit-logs", headers=owner()).json()
    assert rows and all(row["workspace_id"] == "ws_orbit_prod" for row in rows)
    assert all(row["resource_id"] != rivet_id for row in rows)


def test_usage_is_per_workspace(client):
    _seed_two_tenants(client)
    orbit = client.get("/v1/usage", headers=owner()).json()["usage"]
    other = client.get("/v1/usage", headers=rivet()).json()["usage"]
    assert orbit.get("document") == 1 and other.get("document") == 1
    client.post("/v1/query/vector", json={"query": "Zarnotide"}, headers=owner())
    assert client.get("/v1/usage", headers=rivet()).json()["usage"].get("query", 0) == 0


def test_export_and_delete_respect_ownership_and_audit(client):
    orbit_id, _ = _seed_two_tenants(client)
    exported = client.get(f"/v1/assets/{orbit_id}/export", headers=owner())
    assert exported.status_code == 200 and orbit_id in exported.text
    assert "Quantrix" not in exported.text
    assert client.delete(f"/v1/assets/{orbit_id}", headers=owner()).status_code == 204
    # Deleted content must stop being retrievable.
    body = client.post("/v1/query/hybrid", json={"query": "Zarnotide Kelvar"}, headers=owner()).json()
    assert body["results"] == []
    actions = [row["action"] for row in client.get("/v1/audit-logs", headers=owner()).json()]
    assert "asset.exported" in actions and "asset.deletion_requested" in actions
