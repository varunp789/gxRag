# Graph RAG Platform Phase Checklist

Use this file to track delivery progress against [PHASE_PLAN.md](./PHASE_PLAN.md).

## Current Status Summary

- [x] Phase 0: Monorepo Foundation and Initial Setup
- [x] Phase 1: Product and API Definition
- [x] Phase 2: Tenant, Workspace, and Access Foundation
- [x] Phase 3: Unified Asset Registry and Ingestion Entry
- [x] Phase 4: Multi-Format Ingestion Pipeline
- [x] Phase 5: Processing Pipeline
- [x] Phase 6: Index Layer Implementation
- [x] Phase 7: Retrieval API and SDK Layer
- [x] Phase 8: LLM Integration Layer
- [x] Phase 9: Next.js Client/User Portal
- [x] Phase 10: Admin Portal
- [x] Phase 11: SaaS Hardening, Billing, and Governance
- [x] Phase 12: Reliability, Observability, and Launch Readiness

## Phase 0: Monorepo Foundation and Initial Setup

- [x] Create monorepo folder structure
- [x] Add root workspace configuration
- [x] Add root TypeScript base config
- [x] Add environment template
- [x] Add README with local setup instructions
- [x] Scaffold `FastAPI` app
- [x] Add versioned API router
- [x] Add API health endpoint
- [x] Scaffold worker service
- [x] Scaffold `Next.js` frontend
- [x] Add client portal route group
- [x] Add admin portal route group
- [x] Add shared UI package skeleton
- [x] Add TypeScript SDK skeleton
- [x] Add Python SDK skeleton
- [x] Add local Docker Compose infra
- [x] Add architecture docs placeholder
- [x] Validate Python package syntax

## Phase 1: Product and API Definition

- [x] Finalize V1 product packaging
- [x] Finalize pricing and usage units
- [x] Finalize V1 supported source types
- [x] Finalize V1 retrieval modes
- [x] Finalize admin operations scope
- [x] Define canonical asset output contract
- [x] Define query request and response contract
- [x] Define API versioning and compatibility policy
- [x] Document customer-facing API scope

## Phase 2: Tenant, Workspace, and Access Foundation

- [x] Design tenant model
- [x] Design workspace model
- [x] Design user membership model
- [x] Design admin user model
- [x] Design role and permission model
- [x] Design API key model
- [x] Design quota and plan model
- [x] Design audit log model
- [x] Create database migrations for access layer
- [x] Implement auth foundation in backend
- [x] Implement workspace scoping in backend
- [x] Add client sign-in and workspace switcher
- [x] Add admin sign-in flow
- [x] Add admin tenant and workspace inspection views

## Phase 3: Unified Asset Registry and Ingestion Entry

- [x] Design normalized asset model
- [x] Design asset versioning model
- [x] Design asset source model
- [x] Design upload tracking model
- [x] Design processing job and job step model
- [x] Design artifact registry model
- [x] Create asset-related migrations
- [x] Implement upload endpoint
- [x] Implement URL ingestion endpoint
- [x] Implement asset status endpoint
- [x] Implement asset list endpoint
- [x] Add client upload flow
- [x] Add asset list page
- [x] Add processing timeline page
- [x] Add admin asset activity views

## Phase 4: Multi-Format Ingestion Pipeline

- [x] Define adapter interface for ingestion sources
- [x] Implement PDF adapter
- [x] Implement image adapter
- [x] Implement audio adapter
- [x] Implement CSV/Excel adapter
- [x] Implement web content adapter
- [x] Standardize normalized raw artifact format
- [x] Standardize source metadata format
- [x] Standardize extraction warning format
- [x] Add admin diagnostics by source type

## Phase 5: Processing Pipeline

- [x] Implement inspect and plan stage
- [x] Implement parse/OCR/STT stage
- [x] Implement normalize and structure stage
- [x] Implement chunking stage
- [x] Implement embedding stage
- [x] Implement entity extraction stage
- [x] Implement relation extraction stage
- [x] Implement graph construction stage
- [x] Implement structured data registration stage
- [x] Add step idempotency support
- [x] Add resumable execution support
- [x] Add retry per step support
- [x] Add artifact versioning support
- [x] Add provenance tracking support
- [x] Add admin job queue monitor
- [x] Add admin artifact inspection view
- [x] Connect processing stages to real parser/OCR/STT providers
- [x] Move execution to worker queue and persistent state

## Phase 6: Index Layer Implementation

- [x] Scaffold vector index storage contract
- [x] Scaffold BM25/keyword index storage contract
- [x] Scaffold graph index storage contract
- [x] Scaffold structured data index storage contract
- [x] Implement vector writer
- [x] Implement keyword writer
- [x] Implement graph writer
- [x] Implement structured data writer
- [x] Add index sync and reconciliation strategy
- [x] Add admin index status diagnostics
- [x] Connect index writers to real storage backends
- [x] Add persistent index reconciliation jobs

## Phase 7: Retrieval API and SDK Layer

- [x] Implement vector retrieval endpoint
- [x] Implement hybrid retrieval endpoint
- [x] Implement graph retrieval endpoint
- [x] Implement multimodal retrieval endpoint
- [x] Implement structured retrieval endpoint
- [x] Implement graph/entity/relation read endpoints
- [x] Finalize response citation format
- [x] Implement TypeScript SDK client methods
- [x] Implement Python SDK client methods
- [x] Add example integration docs
- [x] Build client retrieval playground
- [x] Build admin query log explorer

## Phase 8: LLM Integration Layer

- [x] Design model abstraction layer
- [x] Implement hosted answer generation endpoints
- [x] Implement prompt template layer
- [x] Implement token metering
- [x] Implement answer logging
- [x] Implement response caching strategy
- [x] Add client hosted answer playground
- [x] Add answer history page
- [x] Add admin answer audit page
- [x] Add admin model diagnostics page

## Phase 9: Next.js Client/User Portal

- [x] Build landing page for product positioning
- [x] Build onboarding flow
- [x] Build workspace dashboard
- [x] Build upload page
- [x] Build asset detail page
- [x] Build processing timeline page
- [x] Build graph explorer
- [x] Build structured table explorer
- [x] Build retrieval playground
- [x] Build API keys page
- [x] Build billing and usage page
- [x] Connect frontend to backend API client

## Phase 10: Admin Portal

- [x] Build admin dashboard
- [x] Build tenant directory
- [x] Build tenant detail page
- [x] Build workspace detail page
- [x] Build user and membership page
- [x] Build asset and job explorer
- [x] Build pipeline diagnostics page
- [x] Build artifact inspection page
- [x] Build query and answer audit page
- [x] Build usage and billing oversight page
- [x] Build system health dashboard
- [x] Add admin RBAC guardrails
- [x] Add support action logging

## Phase 11: SaaS Hardening, Billing, and Governance

- [x] Implement rate limiting
- [x] Implement quota enforcement
- [x] Implement usage metering
- [x] Implement secure deletion workflow
- [x] Implement retention policy support
- [x] Implement export support
- [x] Implement webhook security
- [x] Integrate billing provider
- [x] Map billable units to system events
- [x] Add tenant isolation verification checks
- [x] Add secrets management strategy
- [x] Define PII handling policy

## Phase 12: Reliability, Observability, and Launch Readiness

- [x] Add structured logs
- [x] Add traces across API and worker services
- [x] Add dead-letter queue handling
- [x] Add failure diagnostics and step telemetry
- [x] Add reprocessing controls
- [x] Add artifact integrity checks
- [x] Add health dashboards
- [x] Add queue backlog visibility
- [x] Build modality-based evaluation dataset
- [x] Measure extraction quality
- [x] Measure retrieval quality
- [x] Measure graph correctness
- [x] Prepare API and SDK docs
- [x] Prepare onboarding docs
- [x] Prepare incident response runbook

## Notes

- Update this checklist as implementation progresses.
- Convert partially complete items into more granular subtasks when needed.
- Keep phase status aligned with `PHASE_PLAN.md`.

## Production Readiness Follow-up Checklist

Legend: `[x]` implemented **and verified** (tests/CI/local run noted); `[ ]` still open. Items that need a real
environment, live third-party accounts or a human decision stay open even where the code for them exists.

### Infrastructure and Deployment

- [ ] Provision PostgreSQL with the `pgvector` extension. *(Compose uses `pgvector/pgvector:pg17`; target environment not provisioned.)*
- [ ] Provision Redis, OpenSearch, and ArangoDB with durable volumes and backups. *(Compose: volumes + Redis AOF; production backups not configured.)*
- [ ] Verify API and worker connectivity to every configured dependency. *(Verified locally against real PostgreSQL and Redis; OpenSearch/ArangoDB/pgvector never exercised - the index writers are only unit-tested with fakes.)*
- [ ] Build and publish versioned API and worker container images. *(Dockerfiles hardened - non-root, healthcheck; CI builds them; no registry/publish step. Docker daemon was unavailable here, so images were not built locally.)*
- [ ] Configure production environment variables through a secret manager. *(Variables documented in `.env.example`/`docs/deployment.md`; API refuses insecure config outside development.)*
- [ ] Deploy API, worker, and infrastructure with health checks and restart policies. *(Compose has them; no deployed environment.)*
- [ ] Verify worker queue consumption and dead-letter behavior in the deployed environment. *(Verified with a separate API + worker process and real Redis locally, plus dead-letter tests.)*

### Persistence and Data Lifecycle

- [x] Create and run database migrations for tenant, workspace, access, asset, job, artifact, index, usage, and audit records. *(`app/db/migrations/0001-0004`, idempotent runner, tested on PostgreSQL 16.)*
- [x] Replace development JSON/in-memory state with the production database repositories. *(Registry, usage, audit, API keys, billing mapping, webhook dedup. The tenant/user catalog is still seeded from code.)*
- [ ] Verify artifact-object storage, encryption, backup, and restore procedures. *(Artifacts are files on a shared volume; no object storage, encryption or restore drill.)*
- [x] Configure retention periods and run secure-deletion verification against a test workspace. *(`GXRAG_RETENTION_DAYS`, purge job; verified for files, registry rows and PostgreSQL index tables. OpenSearch/ArangoDB deletion requests are untested against live services.)*
- [x] Verify exports include only data belonging to the requesting workspace. *(`tests/test_isolation.py`.)*

### Providers, Billing, and Integrations

- [ ] Configure and verify parser/OCR/STT providers for each supported modality. *(PDF, web, CSV/Excel verified. Image OCR needs `tesseract`, audio needs `GXRAG_OPENAI_API_KEY`; neither verified.)*
- [ ] Configure the hosted LLM provider and validate grounded answer generation. *(Prompt/citation plumbing and the no-evidence short-circuit are tested; no live provider call.)*
- [x] Configure Stripe customer mapping, billing portal, and webhook processing. *(Tenant-to-customer mapping, portal scoped to caller's tenant, signed + de-duplicated webhooks; tested with Stripe mocked - not yet against a live Stripe account.)*
- [x] Configure webhook signing secrets and replay-protection testing. *(Timestamped HMAC, 5-minute tolerance, event-id dedup in PostgreSQL.)*
- [ ] Run index writes and reconciliation against live pgvector, OpenSearch, ArangoDB, and PostgreSQL services. *(Reconciliation logic tested with fakes; the graph writer now writes edges but is untested against a real ArangoDB.)*

### Security and Governance

- [ ] Replace development header-based identity with a production authentication provider. *(Done: JWT bearer + hashed API keys, dev headers rejected in `jwt` mode and the API will not start in production with `dev`. Open: OIDC/IdP integration with key rotation - tokens use a shared HMAC secret.)*
- [x] Enforce RBAC permissions for every customer and administrator action. *(Permission per route; `tests/test_route_coverage.py` proves every route rejects anonymous callers and `tests/test_auth_rbac.py` covers role boundaries.)*
- [x] Persist audit records in the database and restrict audit-log access. *(Append-only table enforced by trigger; scoped endpoints.)*
- [x] Perform tenant-isolation tests for assets, queries, exports, and admin operations. *(`tests/test_isolation.py`.)*
- [x] Run secrets, dependency, and vulnerability scans in CI. *(gitleaks, pip-audit, npm audit in `.github/workflows/ci.yml`; `npm audit` and `pip-audit` are clean locally; workflow has not yet run on GitHub.)*
- [ ] Approve the PII handling, retention, incident-response, and access-review policies. *(Needs a human owner; mechanisms and runbook drafts are in `docs/`.)*

### Quality and Testing

- [x] Add API unit and integration tests for all customer and admin endpoints. *(182 tests incl. PostgreSQL integration; every route is exercised for auth and for no-5xx.)*
- [x] Add worker tests for retries, resumptions, dead-letter routing, and reconciliation. *(`tests/test_pipeline_worker.py`, `tests/test_database.py`.)*
- [ ] Add frontend tests for onboarding, upload, asset inspection, retrieval, and admin workflows. *(Vitest covers the timeline view-model and API client; most portal pages are still static placeholders with no behaviour to test.)*
- [ ] Run end-to-end tests against the full Docker Compose stack. *(`scripts/smoke.py` passes against separately started API + worker + PostgreSQL + Redis, and is wired into CI; the Compose stack itself could not be started here.)*
- [ ] Build the modality-based gold dataset and record extraction-quality results. *(Web, spreadsheet and PDF slices exist; image and audio slices are missing, and extraction is scored only as pass/fail, not field-level F1.)*
- [x] Measure retrieval relevance, graph correctness, and grounded-answer citation coverage. *(`python -m eval.run`. Citation presence is measured; answer faithfulness is not. See caveats in `docs/evaluation.md`.)*
- [x] Establish release thresholds and block releases that fail quality gates. *(`eval/thresholds.json`, enforced in CI and in the test suite.)*

### Operational Acceptance

- [ ] Verify structured logs, trace IDs, health checks, queue backlog, and alerts in the target environment. *(Logs, `X-Trace-Id`, `/v1/ready`, backlog metrics exist; alerts and target environment do not.)*
- [ ] Run a failure-recovery exercise for unavailable indexes and provider errors. *(Index-failure and reconcile paths are tested; no live exercise.)*
- [ ] Run an incident-response tabletop exercise using the runbook.
- [ ] Conduct a beta-launch review and approve the production launch decision.

### Known gaps found while closing this list

- Retrieval previously scored artifact metadata rather than content; it now runs a local engine over extracted text
  (BM25, trigram vectors, hybrid fusion, graph expansion, structured rows). Queries are **not** served from pgvector,
  OpenSearch or ArangoDB yet - those indexes are written but not read.
- Ingestion adapters for image and audio remain flagged `supports_v1=False` (jobs end in `needs_review`).
- Query/answer logs and the answer cache are in-memory; the rate limiter is per process.
- No tenant/user/membership management API; the catalog is seeded.
