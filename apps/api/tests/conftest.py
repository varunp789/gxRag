import base64

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import issue_token

JWT_SECRET = "test-secret-test-secret-test-secret-0123"


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    """Every test gets fresh JSON/artifact storage, no Redis and fake index backends."""
    from app.services import api_keys, asset_registry, governance, job_queue, retrieval

    monkeypatch.setattr(settings, "processing_state_path", str(tmp_path / "state.json"))
    monkeypatch.setattr(settings, "artifact_root", str(tmp_path / "artifacts"))
    monkeypatch.setattr(settings, "database_url", None)
    monkeypatch.setattr(settings, "auth_mode", "dev")
    monkeypatch.setattr(settings, "environment", "development")
    monkeypatch.setattr(settings, "jwt_secret", JWT_SECRET)
    monkeypatch.setattr(settings, "webhook_secret", "whsec_test")
    monkeypatch.setattr(settings, "rate_limit_per_minute", 10_000)
    monkeypatch.setattr(job_queue, "_redis_client", lambda: None)

    class FakeWrite:
        def __init__(self, kind):
            self.kind = kind

        def __call__(self, **kwargs):
            from app.services.index_backends import IndexWriteResult
            size = len(kwargs.get("chunks") or kwargs.get("rows") or kwargs.get("entities") or [])
            return IndexWriteResult(self.kind, "fake", size, f"fake:{self.kind}")

    for name, kind in (("write_vector", "vector"), ("write_keyword", "keyword"),
                       ("write_graph", "graph"), ("write_structured", "structured")):
        monkeypatch.setattr(asset_registry, name, FakeWrite(kind))

    from app.services import retention
    monkeypatch.setattr(retention, "delete_asset_everywhere", lambda **kw: None)
    asset_registry.reset_state()
    api_keys.reset()
    governance.USAGE.clear()
    governance.AUDIT.clear()
    governance.RATE.clear()
    retrieval.QUERY_LOGS.clear()
    retrieval.ANSWER_LOGS.clear()
    retrieval.ANSWER_CACHE.clear()
    monkeypatch.setattr(settings, "openai_api_key", None)
    yield
    asset_registry.reset_state()


@pytest.fixture
def client():
    from app.main import create_application

    return TestClient(create_application())


@pytest.fixture
def jwt_mode(monkeypatch):
    monkeypatch.setattr(settings, "auth_mode", "jwt")


def bearer(email: str, kind: str = "user", **kwargs) -> dict[str, str]:
    return {"Authorization": f"Bearer {issue_token(email, email=email, kind=kind, **kwargs)}"}


def owner(workspace: str = "ws_orbit_prod") -> dict[str, str]:
    return {"X-Actor-Email": "alex@orbit.bio", "X-Workspace-Id": workspace}


def analyst() -> dict[str, str]:
    return {"X-Actor-Email": "sam@orbit.bio", "X-Workspace-Id": "ws_orbit_prod"}


def rivet() -> dict[str, str]:
    return {"X-Actor-Email": "nia@rivet.capital", "X-Workspace-Id": "ws_rivet_trial"}


def b64(text: str) -> str:
    return base64.b64encode(text.encode()).decode()


def run_worker_until_idle(limit: int = 10) -> int:
    from worker.config import settings as worker_settings
    from worker.main import run_once

    worker_settings.poll_timeout_seconds = 0
    processed = 0
    while processed < limit and run_once():
        processed += 1
    return processed


def ingest(client, headers, *, title, text, asset_type="web_page", file_name="page.html", mime="text/html"):
    """Upload content and drive the worker until the job finishes; return the status body."""
    body = {"title": title, "asset_type": asset_type, "file_name": file_name, "mime_type": mime,
            "size_bytes": len(text), "content_base64": b64(text)}
    created = client.post("/v1/assets/upload", json=body, headers=headers)
    assert created.status_code == 200, created.text
    asset_id = created.json()["asset"]["id"]
    queued = client.post(f"/v1/assets/{asset_id}/process", json={"trigger": "test", "content_base64": b64(text)},
                         headers=headers)
    assert queued.status_code == 200, queued.text
    run_worker_until_idle()
    return asset_id, client.get(f"/v1/assets/{asset_id}/status", headers=headers).json()
