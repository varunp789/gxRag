"""End-to-end smoke test against a running API + worker (jwt auth mode).

    GXRAG_JWT_SECRET=... python scripts/smoke.py http://localhost:8000

Exercises: auth rejection, API-key issuance, upload -> worker processing ->
retrieval with citations, tenant isolation, audit trail, and revocation.
"""

from __future__ import annotations

import base64
import sys
import time

import httpx

from app.core.security import issue_token

PAGE = "<p>Orbit Bio Labs develops Zarnotide for the Kelvar pathway. Zarnotide trials ran in Boston.</p>"


def main(base: str) -> None:
    http = httpx.Client(base_url=f"{base}/v1", timeout=30)
    owner = {"Authorization": f"Bearer {issue_token('alex@orbit.bio', email='alex@orbit.bio')}", "X-Workspace-Id": "ws_orbit_prod"}
    other = {"Authorization": f"Bearer {issue_token('nia@rivet.capital', email='nia@rivet.capital')}", "X-Workspace-Id": "ws_rivet_trial"}
    admin = {"Authorization": f"Bearer {issue_token('ops@gxrag.dev', email='ops@gxrag.dev', kind='admin')}"}

    assert http.get("/health").status_code == 200
    assert http.get("/ready").status_code == 200, http.text
    assert http.get("/assets").status_code == 401, "unauthenticated request must be rejected"

    writer = http.post("/api-keys", json={"name": "smoke-writer", "role": "ingestion_writer"}, headers=owner).json()
    reader = http.post("/api-keys", json={"name": "smoke-reader", "role": "retrieval_reader"}, headers=owner).json()
    wkey = {"Authorization": f"Bearer {writer['secret']}"}
    rkey = {"Authorization": f"Bearer {reader['secret']}"}

    content = base64.b64encode(PAGE.encode()).decode()
    body = {"title": "Smoke page", "asset_type": "web_page", "file_name": "smoke.html", "mime_type": "text/html",
            "size_bytes": len(PAGE), "content_base64": content}
    asset_id = http.post("/assets/upload", json=body, headers=wkey).json()["asset"]["id"]
    assert http.post(f"/assets/{asset_id}/process", json={"content_base64": content}, headers=wkey).status_code == 200
    assert http.post("/assets/upload", json=body, headers=rkey).status_code == 403, "reader key must not upload"

    deadline = time.time() + 60
    while time.time() < deadline:
        status = http.get(f"/assets/{asset_id}/status", headers=wkey).json()
        if status["asset_status"] in {"ready", "failed", "review_required"}:
            break
        time.sleep(1)
    assert status["asset_status"] == "ready", f"worker did not finish the job: {status['asset_status']}"

    result = http.post("/query/hybrid", json={"query": "Zarnotide Boston"}, headers=rkey).json()
    assert result["results"] and result["results"][0]["citation"]["asset_id"] == asset_id, result
    assert http.get(f"/assets/{asset_id}", headers=other).status_code == 404, "tenant isolation breach"
    assert http.post("/query/hybrid", json={"query": "Zarnotide"}, headers=other).json()["results"] == []

    actions = {row["action"] for row in http.get("/admin/audit-logs", headers=admin).json()}
    assert {"api_key.created", "asset.uploaded"} <= actions, actions

    assert http.delete(f"/api-keys/{reader['key']['id']}", headers=owner).status_code == 204
    assert http.post("/query/hybrid", json={"query": "x"}, headers=rkey).status_code == 401, "revoked key still works"
    print("smoke ok:", asset_id)


if __name__ == "__main__":
    main(sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8000")
