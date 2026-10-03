"""The release quality gate runs inside the normal test suite."""

from eval import run


def test_quality_gate_passes(client):
    from worker.config import settings as worker_settings
    from worker.main import run_once

    worker_settings.poll_timeout_seconds = 0

    def drain():
        while run_once():
            pass

    ids, extraction = run.ingest_corpus(client, drain)
    assert all(extraction.values()), extraction
    metrics = run.evaluate(client, ids, extraction)
    failures = {k: (metrics[k], v) for k, v in run.THRESHOLDS.items() if metrics[k] < v}
    assert not failures, failures
