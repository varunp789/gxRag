import json
from pathlib import Path

from app.core.config import settings
from app.services import asset_registry, job_queue
from tests.conftest import b64, ingest, owner, run_worker_until_idle

CSV = "name,dose,species\nZarnotide,5mg,mouse\nKelvarin,9mg,rat\n"
PAGE = ("<html><body><h1>Orbit Bio Labs</h1><p>Orbit Bio Labs develops Zarnotide for the Kelvar pathway. "
        "Zarnotide trials ran in Boston.</p></body></html>")


def test_web_asset_runs_end_to_end(client):
    asset_id, status = ingest(client, owner(), title="Launch", text=PAGE)
    assert status["asset_status"] == "ready"
    job = status["current_job"]
    assert job["status"] == "completed"
    assert job["completed_step_count"] == job["step_count"] == 13
    assert {a["artifact_type"] for a in status["artifacts"]} >= {"processing_plan", "content_chunks", "graph_snapshot"}
    assert {i["index_type"] for i in status["indexes"]} == {"vector", "keyword", "graph", "structured"}
    extracted = next(Path(settings.artifact_root).rglob("raw_extracted.md")).read_text()
    assert "Zarnotide" in extracted and "<h1>" not in extracted


def test_pipeline_metadata_reflects_real_counts(client):
    _, status = ingest(client, owner(), title="Launch", text=PAGE)
    chunks = next(a for a in status["artifacts"] if a["artifact_type"] == "content_chunks")
    entities = next(a for a in status["artifacts"] if a["artifact_type"] == "entity_catalog")
    assert chunks["metadata"]["chunk_count"] == "1"
    assert int(entities["metadata"]["entity_count"]) >= 2


def test_spreadsheet_rows_are_extracted_and_queryable(client):
    asset_id, status = ingest(client, owner(), title="Doses", text=CSV, asset_type="spreadsheet",
                              file_name="doses.csv", mime="text/csv")
    assert status["asset_status"] == "ready"
    rows = json.loads(next(Path(settings.artifact_root).rglob("structured_rows.json")).read_text())
    assert [row["name"] for row in rows] == ["Zarnotide", "Kelvarin"]
    body = client.post("/v1/query/structured", json={"query": "Kelvarin rat"}, headers=owner()).json()
    assert body["results"][0]["metadata"]["name"] == "Kelvarin"
    assert body["table_refs"] == [asset_id]
    table = client.get(f"/v1/tables/{asset_id}", headers=owner()).json()
    assert len(table["rows"]) == 2


def test_failed_extraction_dead_letters_and_is_retryable(client):
    body = {"title": "Broken", "asset_type": "document", "file_name": "x.pdf", "mime_type": "application/pdf",
            "size_bytes": 3, "content_base64": b64("not a pdf")}
    asset_id = client.post("/v1/assets/upload", json=body, headers=owner()).json()["asset"]["id"]
    client.post(f"/v1/assets/{asset_id}/process", json={"content_base64": b64("not a pdf")}, headers=owner())
    run_worker_until_idle()
    status = client.get(f"/v1/assets/{asset_id}/status", headers=owner()).json()
    assert status["asset_status"] == "failed"
    job = status["current_job"]
    assert job["status"] == "failed"
    assert job_queue.backlog()["dead_letter"] == 1
    # Operator retry re-queues the same job; it fails again deterministically but is processed.
    retried = client.post(f"/v1/admin/jobs/{job['id']}/retry")
    assert retried.status_code == 200 and retried.json()["status"] == "retrying"
    assert run_worker_until_idle() == 1
    assert client.get("/v1/admin/audit-logs").json()[0]["action"] == "processing_job.retry_requested"


def test_missing_source_content_fails_cleanly(client):
    body = {"title": "No bytes", "asset_type": "web_page", "file_name": "a.html", "mime_type": "text/html", "size_bytes": 1}
    asset_id = client.post("/v1/assets/upload", json=body, headers=owner()).json()["asset"]["id"]
    client.post(f"/v1/assets/{asset_id}/process", json={}, headers=owner())
    run_worker_until_idle()
    status = client.get(f"/v1/assets/{asset_id}/status", headers=owner()).json()
    assert status["asset_status"] == "failed"
    assert "No readable source content" in status["current_job"]["steps"][0]["warnings"][0]


def test_index_backend_failure_is_recorded_and_reconciled(client, monkeypatch):
    calls = {"fail": True}
    original = asset_registry.write_keyword

    def flaky(**kwargs):
        if calls["fail"]:
            raise RuntimeError("opensearch unavailable")
        return original(**kwargs)

    monkeypatch.setattr(asset_registry, "write_keyword", flaky)
    asset_id, status = ingest(client, owner(), title="Launch", text=PAGE)
    assert status["current_job"]["status"] == "completed_with_index_errors"
    keyword = next(i for i in status["indexes"] if i["index_type"] == "keyword")
    assert keyword["status"] == "failed" and "opensearch unavailable" in keyword["metadata"]["last_error"]
    diag = {d["index_type"]: d for d in client.get("/v1/admin/index/diagnostics").json()}
    assert diag["keyword"]["stale_count"] >= 1

    calls["fail"] = False
    queued = client.post("/v1/admin/index/reconcile").json()
    assert len(queued) == 1
    run_worker_until_idle()
    status = client.get(f"/v1/assets/{asset_id}/status", headers=owner()).json()
    assert {i["status"] for i in status["indexes"]} == {"synced"}
    assert job_queue.backlog()["ready"] == 0


def test_run_queued_job_is_idempotent_for_finished_jobs(client):
    asset_id, status = ingest(client, owner(), title="Launch", text=PAGE)
    job_id = status["current_job"]["id"]
    before = len(asset_registry.ARTIFACTS)
    asset_registry.run_queued_job(job_id)  # already completed: must be a no-op
    assert len(asset_registry.ARTIFACTS) == before


def test_queue_spool_roundtrip_and_dedup():
    job_queue.enqueue("job_a")
    job_queue.enqueue("job_a")
    job_queue.enqueue("job_b")
    assert job_queue.backlog()["ready"] == 2
    assert job_queue.dequeue(0) == "job_a"
    assert job_queue.dequeue(0) == "job_b"
    assert job_queue.dequeue(0) is None


def test_worker_run_once_with_empty_queue(client):
    from worker.main import run_once
    assert run_once() is False


def test_reprocessing_creates_new_artifact_version(client):
    asset_id, _ = ingest(client, owner(), title="Launch", text=PAGE)
    client.post(f"/v1/assets/{asset_id}/process", json={"content_base64": b64(PAGE)}, headers=owner())
    run_worker_until_idle()
    versions = sorted(p.name for p in (Path(settings.artifact_root) / "ws_orbit_prod" / asset_id).iterdir())
    assert versions == ["v1", "v2"]


def test_json_store_picks_up_writes_from_another_process(client):
    """API and worker are separate processes: the API must see the worker's results."""
    asset_id, _ = ingest(client, owner(), title="Launch", text=PAGE)
    state = json.loads(Path(settings.processing_state_path).read_text())
    state["assets"][-1]["title"] = "Edited by another process"
    Path(settings.processing_state_path).write_text(json.dumps(state))
    assert client.get(f"/v1/assets/{asset_id}", headers=owner()).json()["asset"]["title"] == "Edited by another process"
