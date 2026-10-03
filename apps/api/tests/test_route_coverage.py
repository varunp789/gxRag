"""Every registered route must be authenticated (unless explicitly public) and must not 500."""

import re

import pytest

from app.main import create_application
from tests.conftest import ingest, owner

PUBLIC = {"/v1/health", "/v1/ready", "/v1/platform/definition", "/v1/platform/api-scope",
          "/v1/platform/query-contract", "/v1/webhooks/{provider}"}
BODIES = {
    "/v1/assets/upload": {"title": "t", "asset_type": "web_page", "file_name": "a.html", "mime_type": "text/html", "size_bytes": 1},
    "/v1/assets/from-url": {"title": "t", "asset_type": "web_page", "url": "https://example.com/a", "mime_type": "text/html"},
    "/v1/api-keys": {"name": "k", "role": "retrieval_reader"},
    "/v1/admin/tenants/{tenant_id}/billing-customer": {"customer_id": "cus_cov1"},
}
routes = sorted(
    (path, method.upper())
    for path, item in create_application().openapi()["paths"].items()
    for method in item
    if method in {"get", "post", "put", "patch", "delete"}
)


def _fill(path: str, asset_id: str) -> str:
    values = {"asset_id": asset_id, "job_id": "job_unknown", "tenant_id": "tenant_orbit", "workspace_id": "ws_orbit_prod",
              "table_id": asset_id, "mode": "hybrid", "key_id": "key_unknown", "provider": "generic"}
    return re.sub(r"{(\w+)}", lambda m: values[m.group(1)], path)


@pytest.mark.parametrize(("path", "method"), routes)
def test_route_requires_authentication(client, jwt_mode, path, method):
    if path in PUBLIC:
        pytest.skip("public by design")
    response = client.request(method, _fill(path, "asset_x"), json=BODIES.get(path, {}) if method != "GET" else None)
    assert response.status_code == 401, f"{method} {path} is reachable without credentials"


@pytest.mark.parametrize(("path", "method"), routes)
def test_route_never_returns_server_error(client, path, method):
    asset_id, _ = ingest(client, owner(), title="Cov", text="<p>Orbit Bio Labs builds Zarnotide.</p>")
    if path == "/v1/webhooks/{provider}":
        pytest.skip("covered by webhook tests")
    headers = {**owner()}
    kwargs = {}
    if path == "/v1/billing/portal":
        kwargs["params"] = {"return_url": "http://localhost:3000/x"}
    if path in BODIES or method in {"POST", "PUT", "PATCH"}:
        kwargs["json"] = BODIES.get(path, {"query": "x"} if ("/query" in path or "/answers" in path) else {})
    response = client.request(method, _fill(path, asset_id), headers=headers, **kwargs)
    if path == "/v1/billing/portal":
        assert response.status_code == 503  # Stripe intentionally unconfigured in tests
        return
    assert response.status_code < 500, f"{method} {path} -> {response.status_code}: {response.text[:200]}"


def test_route_inventory_is_not_empty():
    assert len(routes) > 40 and ("/v1/assets", "GET") in routes
