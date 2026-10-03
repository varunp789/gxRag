from tests.conftest import owner


def _create(client, role="retrieval_reader", headers=None):
    response = client.post("/v1/api-keys", json={"name": "ci", "role": role}, headers=headers or owner())
    assert response.status_code == 201, response.text
    return response.json()


def test_key_secret_returned_once_and_never_listed(client):
    created = _create(client)
    assert created["secret"].startswith("gxk_")
    listed = client.get("/v1/api-keys", headers=owner()).json()
    assert created["key"]["id"] in {k["id"] for k in listed}
    assert created["secret"] not in str(listed)


def test_machine_keys_cannot_hold_management_roles(client):
    response = client.post("/v1/api-keys", json={"name": "x", "role": "workspace_owner"}, headers=owner())
    assert response.status_code == 422


def test_key_authenticates_within_role(client, jwt_mode, monkeypatch):
    # Create the key through dev-mode owner identity, then use it under jwt mode.
    from app.core.config import settings
    monkeypatch.setattr(settings, "auth_mode", "dev")
    secret = _create(client)["secret"]
    monkeypatch.setattr(settings, "auth_mode", "jwt")
    headers = {"Authorization": f"Bearer {secret}"}
    assert client.get("/v1/assets", headers=headers).status_code == 200
    assert client.post("/v1/query/vector", json={"query": "orbit"}, headers=headers).status_code == 200
    body = {"title": "t", "asset_type": "web_page", "file_name": "a.html", "mime_type": "text/html", "size_bytes": 1}
    assert client.post("/v1/assets/upload", json=body, headers=headers).status_code == 403
    assert client.get("/v1/api-keys", headers=headers).status_code == 403
    assert client.get("/v1/workspaces", headers=headers).status_code == 403  # not a user identity


def test_key_is_bound_to_its_workspace(client, monkeypatch):
    from app.core.config import settings
    secret = _create(client)["secret"]
    monkeypatch.setattr(settings, "auth_mode", "jwt")
    headers = {"Authorization": f"Bearer {secret}"}
    assert client.get("/v1/assets", headers={**headers, "X-Workspace-Id": "ws_orbit_research"}).status_code == 403
    assert client.get("/v1/assets", headers={**headers, "X-Workspace-Id": "ws_rivet_trial"}).status_code == 403


def test_revoked_and_tampered_keys_fail(client, monkeypatch):
    from app.core.config import settings
    created = _create(client)
    live = _create(client)
    assert client.delete(f"/v1/api-keys/{created['key']['id']}", headers=owner()).status_code == 204
    assert client.delete(f"/v1/api-keys/{created['key']['id']}", headers=owner()).status_code == 404
    monkeypatch.setattr(settings, "auth_mode", "jwt")
    assert client.get("/v1/assets", headers={"Authorization": f"Bearer {created['secret']}"}).status_code == 401
    tampered = live["secret"][:-3] + "AAA"
    assert client.get("/v1/assets", headers={"Authorization": f"Bearer {tampered}"}).status_code == 401
    assert client.get("/v1/assets", headers={"Authorization": "Bearer gxk_deadbeef_nope"}).status_code == 401


def test_cannot_revoke_another_workspaces_key(client):
    from tests.conftest import rivet
    created = _create(client)
    assert client.delete(f"/v1/api-keys/{created['key']['id']}", headers=rivet()).status_code == 404
    assert any(k["id"] == created["key"]["id"] for k in client.get("/v1/api-keys", headers=owner()).json())


def test_key_lifecycle_is_audited_with_actor(client):
    created = _create(client)
    client.delete(f"/v1/api-keys/{created['key']['id']}", headers=owner())
    actions = {(row["action"], row["actor"]) for row in client.get("/v1/audit-logs", headers=owner()).json()}
    assert ("api_key.created", "alex@orbit.bio") in actions
    assert ("api_key.revoked", "alex@orbit.bio") in actions
