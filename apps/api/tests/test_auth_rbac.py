import time

import pytest

from app.core.config import Settings, settings
from app.core.security import TokenError, decode_token, issue_token
from tests.conftest import JWT_SECRET, analyst, bearer, owner


def test_health_is_public(client, jwt_mode):
    assert client.get("/v1/health").json()["status"] == "ok"


def test_jwt_mode_rejects_missing_and_dev_headers(client, jwt_mode):
    assert client.get("/v1/workspaces").status_code == 401
    # Dev identity headers must be ignored when real auth is on.
    assert client.get("/v1/workspaces", headers={"X-Actor-Email": "alex@orbit.bio"}).status_code == 401
    assert client.get("/v1/admin/tenants", headers={"X-Admin-Email": "ops@gxrag.dev"}).status_code == 401


def test_jwt_valid_user_token(client, jwt_mode):
    response = client.get("/v1/workspaces", headers=bearer("alex@orbit.bio"))
    assert response.status_code == 200
    assert {w["id"] for w in response.json()} == {"ws_orbit_prod", "ws_orbit_research"}


@pytest.mark.parametrize("mutate", ["expired", "bad_signature", "wrong_issuer", "alg_none", "garbage"])
def test_jwt_rejects_untrusted_tokens(client, jwt_mode, mutate):
    if mutate == "expired":
        token = issue_token("alex@orbit.bio", email="alex@orbit.bio", ttl_seconds=-3600)
    elif mutate == "bad_signature":
        token = issue_token("alex@orbit.bio", email="alex@orbit.bio", secret="x" * 40)
    elif mutate == "wrong_issuer":
        token = issue_token("alex@orbit.bio", email="alex@orbit.bio", issuer="evil")
    elif mutate == "alg_none":
        import base64
        import json
        enc = lambda d: base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()
        token = f"{enc({'alg': 'none'})}.{enc({'sub': 'a', 'email': 'alex@orbit.bio', 'iss': 'gxrag', 'exp': time.time() + 99})}."
    else:
        token = "not-a-token"
    response = client.get("/v1/workspaces", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_decode_token_roundtrip_and_errors():
    claims = decode_token(issue_token("u1", email="a@b.c"), secret=JWT_SECRET)
    assert claims["sub"] == "u1"
    with pytest.raises(TokenError):
        decode_token("a.b", secret=JWT_SECRET)


def test_unknown_user_token_is_unauthorized(client, jwt_mode):
    assert client.get("/v1/workspaces", headers=bearer("ghost@nowhere.io")).status_code == 401


def test_user_token_cannot_reach_admin_and_admin_cannot_reach_workspace(client, jwt_mode):
    assert client.get("/v1/admin/tenants", headers=bearer("alex@orbit.bio")).status_code == 403
    admin = bearer("ops@gxrag.dev", kind="admin")
    assert client.get("/v1/admin/tenants", headers=admin).status_code == 200
    assert client.get("/v1/assets", headers=admin).status_code == 403


def test_analyst_can_read_and_query_but_not_write(client):
    assert client.get("/v1/assets", headers=analyst()).status_code == 200
    assert client.post("/v1/query/hybrid", json={"query": "x"}, headers=analyst()).status_code == 200
    body = {"title": "t", "asset_type": "web_page", "file_name": "a.html", "mime_type": "text/html", "size_bytes": 1}
    assert client.post("/v1/assets/upload", json=body, headers=analyst()).status_code == 403
    assert client.post("/v1/assets/asset_orbit_trial_pdf/process", json={}, headers=analyst()).status_code == 403
    assert client.delete("/v1/assets/asset_orbit_trial_pdf", headers=analyst()).status_code == 403
    assert client.get("/v1/assets/asset_orbit_trial_pdf/export", headers=analyst()).status_code == 403
    assert client.get("/v1/api-keys", headers=analyst()).status_code == 403
    assert client.post("/v1/api-keys", json={"name": "k"}, headers=analyst()).status_code == 403
    assert client.post("/v1/billing/portal", params={"customer_id": "c", "return_url": "https://x"},
                       headers=analyst()).status_code == 403


def test_owner_has_workspace_permissions(client):
    assert client.get("/v1/usage", headers=owner()).status_code == 200
    assert client.get("/v1/api-keys", headers=owner()).status_code == 200


def test_support_admin_cannot_operate_or_read_audit(client, monkeypatch):
    from app.models.access import AdminUser
    from app.services import catalog

    monkeypatch.setattr(catalog, "ADMIN_USERS", [*catalog.ADMIN_USERS,
                        AdminUser(id="a2", email="support@gxrag.dev", full_name="S", roles=["support_admin"])])
    headers = {"X-Admin-Email": "support@gxrag.dev"}
    assert client.get("/v1/admin/jobs", headers=headers).status_code == 200
    assert client.post("/v1/admin/jobs/job_x/retry", headers=headers).status_code == 403
    assert client.post("/v1/admin/index/reconcile", headers=headers).status_code == 403
    assert client.get("/v1/admin/audit-logs", headers=headers).status_code == 403
    assert client.get("/v1/admin/audit-logs").status_code == 200  # default platform_admin (dev)


def test_runtime_config_validation(monkeypatch):
    Settings(environment="development", auth_mode="dev").validate_for_runtime()
    with pytest.raises(RuntimeError, match="AUTH_MODE"):
        Settings(environment="production", auth_mode="dev").validate_for_runtime()
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        Settings(environment="production", auth_mode="jwt", jwt_secret="short").validate_for_runtime()
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        Settings(environment="production", auth_mode="jwt", jwt_secret="x" * 40).validate_for_runtime()
    Settings(environment="production", auth_mode="jwt", jwt_secret="x" * 40,
             database_url="postgresql://x/y").validate_for_runtime()


def test_docs_hidden_outside_development(monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import create_application

    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "auth_mode", "jwt")
    monkeypatch.setattr(settings, "database_url", "postgresql://unused/unused")
    assert TestClient(create_application()).get("/docs").status_code == 404
