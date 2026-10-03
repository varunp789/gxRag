import time

from app.core.config import settings
from app.services import catalog
from app.services.governance import sign_webhook
from tests.conftest import analyst, ingest, owner, rivet

BODY = {"title": "t", "asset_type": "web_page", "file_name": "a.html", "mime_type": "text/html", "size_bytes": 1}


def _hook(client, payload: bytes, signature: str, provider="generic", header="X-Gxrag-Signature"):
    return client.post(f"/v1/webhooks/{provider}", content=payload, headers={header: signature})


def test_webhook_signature_required_and_verified(client):
    payload = b'{"id":"evt_1","type":"x"}'
    assert client.post("/v1/webhooks/generic", content=payload).status_code == 401
    assert _hook(client, payload, "bad").status_code == 401
    assert _hook(client, payload, "t=abc,v1=00").status_code == 401
    assert _hook(client, payload, sign_webhook(payload, "other")).status_code == 401
    assert _hook(client, payload, sign_webhook(payload, "whsec_test")).status_code == 202
    # A valid signature over a different body must not validate this body.
    other = b'{"id":"evt_2","type":"x"}'
    assert _hook(client, other, sign_webhook(payload, "whsec_test")).status_code == 401


def test_webhook_rejects_stale_timestamps_and_duplicate_events(client):
    payload = b'{"id":"evt_9","type":"invoice.paid"}'
    old = sign_webhook(payload, "whsec_test", timestamp=int(time.time()) - 3600)
    assert _hook(client, payload, old).status_code == 401  # replayed capture
    fresh = sign_webhook(payload, "whsec_test")
    assert _hook(client, payload, fresh).json() == {"accepted": True, "duplicate": False}
    assert _hook(client, payload, sign_webhook(payload, "whsec_test")).json() == {"accepted": True, "duplicate": True}
    assert [r["action"] for r in client.get("/v1/admin/audit-logs").json()].count("webhook.invoice.paid") == 1


def test_webhook_requires_event_id_and_json(client):
    for body in (b"not json", b'{"type":"x"}', b"[]"):
        assert _hook(client, body, sign_webhook(body, "whsec_test")).status_code == 400


def test_webhook_without_configured_secret_fails_closed(client, monkeypatch):
    monkeypatch.setattr(settings, "webhook_secret", None)
    body = b'{"id":"e"}'
    assert _hook(client, body, sign_webhook(body, "")).status_code == 401


def test_stripe_webhook_uses_its_own_secret_and_header(client):
    body = b'{"id":"evt_s","type":"customer.subscription.updated","data":{"object":{"customer":"cus_123"}}}'
    assert _hook(client, body, sign_webhook(body, "whsec_test"), "stripe", "Stripe-Signature").status_code == 401
    assert _hook(client, body, sign_webhook(body, "whsec_stripe"), "stripe", "Stripe-Signature").status_code == 202
    assert _hook(client, body, sign_webhook(body, "whsec_stripe"), "stripe", "X-Gxrag-Signature").status_code == 401


def test_stripe_event_is_attributed_to_the_linked_tenant(client):
    assert client.put("/v1/admin/tenants/tenant_orbit/billing-customer", json={"customer_id": "cus_orbit1"}).status_code == 204
    body = b'{"id":"evt_t","type":"invoice.payment_failed","data":{"object":{"customer":"cus_orbit1"}}}'
    _hook(client, body, sign_webhook(body, "whsec_stripe"), "stripe", "Stripe-Signature")
    row = next(r for r in client.get("/v1/admin/audit-logs").json() if r["action"] == "webhook.invoice.payment_failed")
    assert row["resource_type"] == "tenant" and row["resource_id"] == "tenant_orbit"


def test_billing_customer_link_validation(client):
    link = lambda tenant, cid: client.put(f"/v1/admin/tenants/{tenant}/billing-customer", json={"customer_id": cid})  # noqa: E731
    assert link("tenant_orbit", "bad id").status_code == 422
    assert link("tenant_nope", "cus_x1").status_code == 409
    assert link("tenant_orbit", "cus_shared").status_code == 204
    assert link("tenant_rivet", "cus_shared").status_code == 409  # one customer, one tenant


def test_document_quota_enforced_per_plan(client, monkeypatch):
    plan = next(p for p in catalog.PLANS if p.id == "plan_growth")
    monkeypatch.setattr(plan, "monthly_document_limit", 2)
    assert client.post("/v1/assets/upload", json=BODY, headers=owner()).status_code == 200
    assert client.post("/v1/assets/upload", json=BODY, headers=owner()).status_code == 200
    third = client.post("/v1/assets/upload", json=BODY, headers=owner())
    assert third.status_code == 429 and "quota" in third.json()["detail"]
    # Other workspaces on other plans are unaffected.
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


def test_billing_portal_flow_and_guards(client, monkeypatch):
    portal = lambda headers=None, url="http://localhost:3000/billing": client.post(  # noqa: E731
        "/v1/billing/portal", params={"return_url": url}, headers=headers or owner())
    assert portal().status_code == 503  # Stripe not configured
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_x")
    assert portal().status_code == 409  # tenant has no linked customer
    client.put("/v1/admin/tenants/tenant_orbit/billing-customer", json={"customer_id": "cus_orbit1"})
    assert portal(url="https://evil.example/steal").status_code == 422  # open-redirect guard

    seen = {}

    class Reply:
        def raise_for_status(self): pass
        def json(self): return {"url": "https://billing.stripe.test/session"}

    def fake_post(url, headers, data, timeout):
        seen.update(data)
        return Reply()

    monkeypatch.setattr("app.services.governance.httpx.post", fake_post)
    assert portal().json() == {"url": "https://billing.stripe.test/session"}
    assert seen["customer"] == "cus_orbit1"
    # A client-supplied customer id is ignored: Rivet cannot reach Orbit's customer.
    response = client.post("/v1/billing/portal", params={"return_url": "http://localhost:3000/b", "customer_id": "cus_orbit1"},
                           headers=rivet())
    assert response.status_code == 409
    assert client.post("/v1/billing/portal", params={"return_url": "http://localhost:3000/b"}, headers=analyst()).status_code == 403


def test_rate_limit_table_is_bounded(client, monkeypatch):
    from app.services import governance
    monkeypatch.setattr(settings, "rate_limit_per_minute", 5)
    for index in range(10_050):
        governance.RATE[f"stale{index}"] = [time.time() - 120]
    assert client.get("/v1/workspaces", headers={"Authorization": "Bearer random-token"}).status_code in {200, 401, 429}
    assert len(governance.RATE) < 100


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
