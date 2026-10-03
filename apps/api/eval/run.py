"""Release quality gate: python -m eval.run [--json out.json]

Ingests the gold corpus through the real API + worker, then measures extraction
success, retrieval recall@5 / MRR per mode, graph correctness and citation
coverage, and exits non-zero when any metric misses eval/thresholds.json.
"""

from __future__ import annotations

import base64
import json
import sys
import tempfile
from pathlib import Path

from eval import corpus

THRESHOLDS = json.loads((Path(__file__).parent / "thresholds.json").read_text())
HEADERS = {"X-Actor-Email": "alex@orbit.bio", "X-Workspace-Id": "ws_orbit_prod"}


def _b64(raw: bytes | str) -> str:
    return base64.b64encode(raw if isinstance(raw, bytes) else raw.encode()).decode()


def ingest_corpus(client, run_worker) -> tuple[dict[str, str], dict[str, bool]]:
    """Return ({key: asset_id}, {key: extraction_ok})."""
    items: list[tuple[str, str, str, str, bytes | str, str]] = []
    for key, (title, html) in corpus.WEB.items():
        items.append((key, title, "web_page", f"{key}.html", html, "text/html"))
    for key, (title, text) in corpus.CSV.items():
        items.append((key, title, "spreadsheet", f"{key}.csv", text, "text/csv"))
    for key, (title, text) in corpus.PDF_TEXT.items():
        items.append((key, title, "document", f"{key}.pdf", corpus.build_pdf(text), "application/pdf"))
    ids: dict[str, str] = {}
    ok: dict[str, bool] = {}
    for key, title, asset_type, name, content, mime in items:
        body = {"title": title, "asset_type": asset_type, "file_name": name, "mime_type": mime,
                "size_bytes": len(content), "content_base64": _b64(content)}
        asset_id = client.post("/v1/assets/upload", json=body, headers=HEADERS).json()["asset"]["id"]
        client.post(f"/v1/assets/{asset_id}/process", json={"content_base64": _b64(content)}, headers=HEADERS)
        ids[key] = asset_id
    run_worker()
    for key, asset_id in ids.items():
        ok[key] = client.get(f"/v1/assets/{asset_id}/status", headers=HEADERS).json()["asset_status"] == "ready"
    return ids, ok


def evaluate(client, ids: dict[str, str], extraction: dict[str, bool]) -> dict[str, float]:
    by_asset = {asset_id: key for key, asset_id in ids.items()}
    hits = reciprocal = counted = 0.0
    citations_total = citations_valid = 0
    per_mode: dict[str, list[float]] = {}
    for text, mode, expected in corpus.QUERIES:
        body = client.post(f"/v1/query/{mode}", json={"query": text, "limit": 5}, headers=HEADERS).json()
        ranked = []
        for result in body["results"]:
            key = by_asset.get(result["citation"]["asset_id"])
            if key and key not in ranked:
                ranked.append(key)
            citations_total += 1
            cite = result["citation"]
            citations_valid += int(bool(cite["asset_id"] in by_asset and cite["artifact_id"] and cite["provenance"]))
        found = [rank for rank, key in enumerate(ranked, start=1) if key in expected]
        hit = bool(found)
        hits += hit
        reciprocal += 1 / found[0] if found else 0
        counted += 1
        per_mode.setdefault(mode, []).append(float(hit))

    graph_hits = 0
    for text, expected in corpus.GRAPH_QUERIES:
        body = client.post("/v1/query/graph", json={"query": text, "limit": 10}, headers=HEADERS).json()
        reached = {by_asset.get(r["citation"]["asset_id"]) for r in body["results"]}
        graph_hits += int(expected <= reached)

    entity_found = entity_total = relation_found = relation_total = 0
    for key, truth in corpus.GRAPH_TRUTH.items():
        graph = client.get(f"/v1/assets/{ids[key]}/graph", headers=HEADERS).json()
        entities = set(graph["entities"])
        relations = {tuple(sorted(pair)) for pair in graph["relations"]}
        entity_total += len(truth["entities"])
        entity_found += len(truth["entities"] & entities)
        expected_relations = {tuple(sorted(pair)) for pair in truth["relations"]}
        relation_total += len(expected_relations)
        relation_found += len(expected_relations & relations)

    negatives_clean = 0
    for text in corpus.NEGATIVE_QUERIES:
        body = client.post("/v1/query/hybrid", json={"query": text, "limit": 5}, headers=HEADERS).json()
        negatives_clean += int(not body["results"])

    metrics = {
        "retrieval_recall_at_5": hits / counted,
        "retrieval_mrr": reciprocal / counted,
        "graph_entity_recall": entity_found / entity_total,
        "graph_relation_recall": relation_found / relation_total,
        "graph_expansion_recall": graph_hits / len(corpus.GRAPH_QUERIES),
        "citation_coverage": citations_valid / citations_total if citations_total else 0.0,
        "negative_query_precision": negatives_clean / len(corpus.NEGATIVE_QUERIES),
        "extraction_success_rate": sum(extraction.values()) / len(extraction),
    }
    metrics.update({f"recall_at_5[{mode}]": sum(v) / len(v) for mode, v in sorted(per_mode.items())})
    return metrics


def main(argv: list[str]) -> int:
    from fastapi.testclient import TestClient

    from app.core.config import settings
    from app.main import create_application
    from app.services import asset_registry, job_queue
    from app.services.index_backends import IndexWriteResult

    with tempfile.TemporaryDirectory() as workdir:
        settings.processing_state_path = str(Path(workdir) / "state.json")
        settings.artifact_root = str(Path(workdir) / "artifacts")
        settings.database_url = None
        settings.auth_mode = "dev"
        settings.rate_limit_per_minute = 100_000
        job_queue._redis_client = lambda: None  # type: ignore[assignment]
        for name in ("write_vector", "write_keyword", "write_graph", "write_structured"):
            setattr(asset_registry, name, lambda **kw: IndexWriteResult("x", "eval", 0, "eval"))
        asset_registry.reset_state()

        from worker.config import settings as worker_settings
        from worker.main import run_once

        worker_settings.poll_timeout_seconds = 0

        def run_worker() -> None:
            while run_once():
                pass

        client = TestClient(create_application())
        ids, extraction = ingest_corpus(client, run_worker)
        metrics = evaluate(client, ids, extraction)

    failures = {name: (metrics[name], floor) for name, floor in THRESHOLDS.items() if metrics[name] < floor}
    print(f"{'metric':<34}{'value':>8}{'threshold':>11}")
    for name, value in metrics.items():
        floor = THRESHOLDS.get(name)
        flag = "" if floor is None else ("  FAIL" if name in failures else "  ok")
        print(f"{name:<34}{value:>8.3f}{'' if floor is None else f'{floor:>11.2f}'}{flag}")
    print("not_evaluated: image (OCR needs tesseract), audio (STT needs provider key)")
    if "--json" in argv:
        Path(argv[argv.index("--json") + 1]).write_text(json.dumps(
            {"metrics": metrics, "thresholds": THRESHOLDS, "passed": not failures}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
