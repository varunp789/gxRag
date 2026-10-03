# Deployment and operations

## Components

| Component | Image | Notes |
|---|---|---|
| `migrate` | `apps/api/Dockerfile` | `python -m app.db.migrate --seed`; run to completion before API/worker roll out. |
| `api` | `apps/api/Dockerfile` | `uvicorn app.main:app`; probes `/v1/health` (liveness), `/v1/ready` (readiness: database + queue). |
| `worker` | `apps/worker/Dockerfile` | Needs the `tesseract` binary (installed in the image) and the same env as the API. |
| PostgreSQL (pgvector) | | System of record: registry, usage, audit, API keys, vectors, structured rows. |
| Redis | | Job queue (`asset-processing`) with AOF enabled. Without Redis the worker falls back to a local spool - dev only. |
| OpenSearch, ArangoDB | | Keyword and graph indexes. |

API and worker **must share the artifact volume** (`GXRAG_ARTIFACT_ROOT`) until artifact storage moves to
object storage. In Compose this is the `artifacts` volume.

## Required configuration (non-development)

```
GXRAG_ENVIRONMENT=production
GXRAG_AUTH_MODE=jwt
GXRAG_JWT_SECRET=<>= 32 random chars, from the secret manager>
GXRAG_DATABASE_URL=postgresql://...
GXRAG_REDIS_URL=redis://...
GXRAG_WEBHOOK_SECRET=<random>
GXRAG_STRIPE_SECRET_KEY / GXRAG_STRIPE_WEBHOOK_SECRET   # billing
GXRAG_OPENAI_API_KEY                                    # hosted answers + audio STT
GXRAG_BILLING_RETURN_ORIGINS=["https://app.example.com"]
GXRAG_RETENTION_DAYS=30
```

The API exits at startup if the auth/database settings are insecure or missing.

## Release procedure

1. CI green (`api`, `web`, `sdk-python`, `e2e`, `security`, `images`, and the evaluation gate inside `api`).
2. Build and tag images (`gxrag-api:<sha>`, `gxrag-worker:<sha>`).
3. Run the `migrate` job against the target database. Migrations are forward-only, idempotent and recorded
   in `schema_migrations`; they take an advisory lock so concurrent runs are safe.
4. Roll out the worker, then the API. Wait for `/v1/ready` = 200.
5. Run `python apps/api/scripts/smoke.py <base-url>` with an operator-minted JWT secret.

**Rollback:** redeploy the previous images. Migrations are additive (new tables/columns), so the previous
version keeps working against the newer schema; never drop columns in the same release that stops using them.

## Scheduled jobs

* Retention: `python -m app.services.retention` daily (or `POST /v1/admin/retention/run`). Purges soft-deleted
  assets older than `GXRAG_RETENTION_DAYS` from artifacts, every index backend and the registry. Failures are
  reported in the response/logs and retried on the next run.
* Index reconciliation: `POST /v1/admin/index/reconcile` re-queues assets with failed or stale index records.

## Backup and restore

* PostgreSQL: nightly `pg_dump` plus WAL archiving; restore by creating a database, loading the dump, and
  running `app.db.migrate` (no-op when current). Verify with `scripts/smoke.py`.
* Artifacts: snapshot the artifact volume/bucket with the same cadence; derived indexes can be rebuilt from
  artifacts with `reconcile`.
* Redis: AOF is on; queued job ids are also recoverable from `processing_jobs` rows in `queued`/`retrying` state.
* A restore drill has **not** been performed - see the production-readiness checklist.

## Observability

* Structured JSON logs on stdout: `http.request`, `http.response`, `worker.job.finished`, `retention.purge_failed`,
  each with `trace_id`. Clients may send `X-Trace-Id`; it is echoed on the response.
* `GET /v1/admin/health` reports queue backlog (`ready`, `dead_letter`) and artifact integrity.
* Suggested alerts: `/v1/ready` non-200, `dead_letter` > 0, `ready` backlog growing for 10 minutes,
  `retention.purge_failed` present, 5xx ratio.

## Local stack

```bash
docker compose -f infra/docker-compose.yml up -d --build
```

Starts all backing services, runs `migrate`, then the API (dev auth) on :8000 and the worker.
