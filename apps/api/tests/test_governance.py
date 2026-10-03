import hashlib
import hmac

from app.core.config import settings
from app.services import catalog
from tests.conftest import analyst, ingest, owner

BODY = {"title": "t", "asset_type": "web_page", "file_name": "a.html", "mime_type": "text/html", "size_bytes": 1}


def _sign(payload: bytes, secret="whsec_test") -> str:
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def test_webhook_signature_required_and_verified(client):
    payload = b'{"event":"x"}'
    assert client.post("/v1/webhooks/stripe", content=payload).status_code == 401
    assert client.post("/v1/webhooks/stripe", content=payload, headers={"X-Gxrag-Signature": "bad"}).status_code == 401
    assert client.post("/v1/webhooks/stripe", content=payload,
                       headers={"X-Gxrag-Signature": _sign(payload, "other")}).status_code == 401
    ok = client.post("/v1/webhooks/stripe", content=payload, headers={"X-Gxrag-Signature": _sign(payload)})
    assert ok.status_code == 202
    # A valid signature over a different body must not validate this body.
    assert client.post("/v1/webhooks/stripe", content=b'{"event":"y"}',
                       headers={"X-Gxrag-Signature": _sign(payload)}).status_code == 401


def test_webhook_without_configured_secret_fails_closed(client, monkeypatch):
    monkeypatch.setattr(settings, "webhook_secret", None)
    assert client.post("/v1/webhooks/stripe", content=b"{}", headers={"X-Gxrag-Signature": "x"}).status_code == 401


def test_document_quota_enforced_per_plan(client, monkeypatch):
    plan = next(p for p in catalog.PLANS if p.id == "plan_growth")
    monkeypatch.setattr(plan, "monthly_document_limit", 2)
    assert client.post("/v1/assets/upload", json=BODY, headers=owner()).status_code == 200
    assert client.post("/v1/assets/upload", json=BODY, headers=owner()).status_code == 200
    third = client.post("/v1/assets/upload", json=BODY, headers=owner())
    assert third.status_code == 429 and "quota" in third.json()["detail"]
    # Other workspaces on other plans are unaffected.
    from tests.conftest import rivet
    assert client.post("/v1/assets/upload", json=BODY, headers=rivet()).status_code == 200


def test_query_quota_enforced(client, monkeypatch):
    plan = next(p for p in catalog.PLANS if p.id == "plan_growth")
    monkeypatch.setattr(plan, "monthly_query_limit", 1)
    assert client.post("/v1/query/vector", json={"query": "x"}, headers=owner()).status_code == 200
    assert client.post("/v1/query/vector", json={"query": "x"}, headers=owner()).status_code == 429


def test_usage_resets_when_the_month_rolls_over(client, monkeypatch):
    from app.db import store

    client.post("/v1/query/vector", json={"query": "x"}, headers=owner())
    assert client.get("/v1/usage", headers=owner()).json()["usage"]["query"] == 1
    monkeypatch.setattr(store, "current_period", lambda now=None: "2099-01")
    assert client.get("/v1/usage", headers=owner()).json()["usage"] == {}


def test_rate_limit(client, monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_per_minute", 3)
    codes = [client.get("/v1/workspaces", headers=owner()).status_code for _ in range(5)]
    assert codes[:3] == [200, 200, 200] and codes[3:] == [429, 429]
    # A different caller has its own budget.
    assert client.get("/v1/workspaces", headers=analyst()).status_code == 200


def test_trace_id_is_propagated(client):
    response = client.get("/v1/health", headers={"X-Trace-Id": "trace-123"})
    assert response.headers["X-Trace-Id"] == "trace-123"
    assert client.get("/v1/health").headers["X-Trace-Id"]


def test_billing_portal_requires_stripe_config(client):
    response = client.post("/v1/billing/portal", params={"customer_id": "c", "return_url": "https://x"},
                           headers=owner())
    assert response.status_code == 503


def test_deletion_redacts_source_and_blocks_retrieval(client):
    asset_id, _ = ingest(client, owner(), title="Secret", text="Confidential Project Nightjar budget figures.")
    assert client.post("/v1/query/hybrid", json={"query": "Nightjar"}, headers=owner()).json()["results"]
    assert client.delete(f"/v1/assets/{asset_id}", headers=owner()).status_code == 204
    assert client.post("/v1/query/hybrid", json={"query": "Nightjar"}, headers=owner()).json()["results"] == []
    source = client.get(f"/v1/assets/{asset_id}", headers=owner()).json()["source"]
    assert source["location"] == "deleted://redacted"


def test_readiness_endpoint(client):
    response = client.get("/v1/ready")
    assert response.status_code == 200 and response.json()["checks"]["queue"] == "ok"


def test_admin_health_reports_queue_and_integrity(client):
    body = client.get("/v1/admin/health").json()
    assert body["queue"] == {"ready": 0, "dead_letter": 0}
