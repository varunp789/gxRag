# Graph RAG Platform Phase Checklist

Use this file to track delivery progress against [PHASE_PLAN.md](./PHASE_PLAN.md).

## Current Status Summary

- [x] Phase 0: Monorepo Foundation and Initial Setup
- [x] Phase 1: Product and API Definition
- [ ] Phase 2: Tenant, Workspace, and Access Foundation
- [ ] Phase 3: Unified Asset Registry and Ingestion Entry
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
- [ ] Create database migrations for access layer
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
- [ ] Create asset-related migrations
- [x] Implement upload endpoint
- [x] Implement URL ingestion endpoint
- [x] Implement asset status endpoint
- [x] Implement asset list endpoint
- [x] Add client upload flow
- [x] Add asset list page
- [ ] Add processing timeline page
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

The phase deliverables are implemented, but the following work must be completed
and verified before treating the service as production-ready.

### Infrastructure and Deployment

- [ ] Provision PostgreSQL with the `pgvector` extension.
- [ ] Provision Redis, OpenSearch, and ArangoDB with durable volumes and backups.
- [ ] Verify API and worker connectivity to every configured dependency.
- [ ] Build and publish versioned API and worker container images.
- [ ] Configure production environment variables through a secret manager.
- [ ] Deploy API, worker, and infrastructure with health checks and restart policies.
- [ ] Verify worker queue consumption and dead-letter behavior in the deployed environment.

### Persistence and Data Lifecycle

- [ ] Create and run database migrations for tenant, workspace, access, asset, job, artifact, index, usage, and audit records.
- [ ] Replace development JSON/in-memory state with the production database repositories.
- [ ] Verify artifact-object storage, encryption, backup, and restore procedures.
- [ ] Configure retention periods and run secure-deletion verification against a test workspace.
- [ ] Verify exports include only data belonging to the requesting workspace.

### Providers, Billing, and Integrations

- [ ] Configure and verify parser/OCR/STT providers for each supported modality.
- [ ] Configure the hosted LLM provider and validate grounded answer generation.
- [ ] Configure Stripe customer mapping, billing portal, and webhook processing.
- [ ] Configure webhook signing secrets and replay-protection testing.
- [ ] Run index writes and reconciliation against live pgvector, OpenSearch, ArangoDB, and PostgreSQL services.

### Security and Governance

- [ ] Replace development header-based identity with a production authentication provider.
- [ ] Enforce RBAC permissions for every customer and administrator action.
- [ ] Persist audit records in the database and restrict audit-log access.
- [ ] Perform tenant-isolation tests for assets, queries, exports, and admin operations.
- [ ] Run secrets, dependency, and vulnerability scans in CI.
- [ ] Approve the PII handling, retention, incident-response, and access-review policies.

### Quality and Testing

- [ ] Add API unit and integration tests for all customer and admin endpoints.
- [ ] Add worker tests for retries, resumptions, dead-letter routing, and reconciliation.
- [ ] Add frontend tests for onboarding, upload, asset inspection, retrieval, and admin workflows.
- [ ] Run end-to-end tests against the full Docker Compose stack.
- [ ] Build the modality-based gold dataset and record extraction-quality results.
- [ ] Measure retrieval relevance, graph correctness, and grounded-answer citation coverage.
- [ ] Establish release thresholds and block releases that fail quality gates.

### Operational Acceptance

- [ ] Verify structured logs, trace IDs, health checks, queue backlog, and alerts in the target environment.
- [ ] Run a failure-recovery exercise for unavailable indexes and provider errors.
- [ ] Run an incident-response tabletop exercise using the runbook.
- [ ] Conduct a beta-launch review and approve the production launch decision.
