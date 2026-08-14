# Graph RAG Platform Phase Checklist

Use this file to track delivery progress against [PHASE_PLAN.md](./PHASE_PLAN.md).

## Current Status Summary

- [x] Phase 0: Monorepo Foundation and Initial Setup
- [x] Phase 1: Product and API Definition
- [ ] Phase 2: Tenant, Workspace, and Access Foundation
- [ ] Phase 3: Unified Asset Registry and Ingestion Entry
- [x] Phase 4: Multi-Format Ingestion Pipeline
- [ ] Phase 5: Processing Pipeline
- [ ] Phase 6: Index Layer Implementation
- [ ] Phase 7: Retrieval API and SDK Layer
- [ ] Phase 8: LLM Integration Layer
- [ ] Phase 9: Next.js Client/User Portal
- [ ] Phase 10: Admin Portal
- [ ] Phase 11: SaaS Hardening, Billing, and Governance
- [ ] Phase 12: Reliability, Observability, and Launch Readiness

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

- [ ] Implement inspect and plan stage
- [ ] Implement parse/OCR/STT stage
- [ ] Implement normalize and structure stage
- [ ] Implement chunking stage
- [ ] Implement embedding stage
- [ ] Implement entity extraction stage
- [ ] Implement relation extraction stage
- [ ] Implement graph construction stage
- [ ] Implement structured data registration stage
- [ ] Add step idempotency support
- [ ] Add resumable execution support
- [ ] Add retry per step support
- [ ] Add artifact versioning support
- [ ] Add provenance tracking support
- [ ] Add admin job queue monitor
- [ ] Add admin artifact inspection view

## Phase 6: Index Layer Implementation

- [ ] Set up vector index storage
- [ ] Set up BM25/keyword index storage
- [ ] Set up graph index storage
- [ ] Set up structured data index storage
- [ ] Implement vector writer
- [ ] Implement keyword writer
- [ ] Implement graph writer
- [ ] Implement structured data writer
- [ ] Add index sync and reconciliation strategy
- [ ] Add admin index status diagnostics

## Phase 7: Retrieval API and SDK Layer

- [ ] Implement vector retrieval endpoint
- [ ] Implement hybrid retrieval endpoint
- [ ] Implement graph retrieval endpoint
- [ ] Implement multimodal retrieval endpoint
- [ ] Implement structured retrieval endpoint
- [ ] Implement graph/entity/relation read endpoints
- [ ] Finalize response citation format
- [ ] Implement TypeScript SDK client methods
- [ ] Implement Python SDK client methods
- [ ] Add example integration docs
- [ ] Build client retrieval playground
- [ ] Build admin query log explorer

## Phase 8: LLM Integration Layer

- [ ] Design model abstraction layer
- [ ] Implement hosted answer generation endpoints
- [ ] Implement prompt template layer
- [ ] Implement token metering
- [ ] Implement answer logging
- [ ] Implement response caching strategy
- [ ] Add client hosted answer playground
- [ ] Add answer history page
- [ ] Add admin answer audit page
- [ ] Add admin model diagnostics page

## Phase 9: Next.js Client/User Portal

- [ ] Build landing page for product positioning
- [ ] Build onboarding flow
- [ ] Build workspace dashboard
- [ ] Build upload page
- [ ] Build asset detail page
- [ ] Build processing timeline page
- [ ] Build graph explorer
- [ ] Build structured table explorer
- [ ] Build retrieval playground
- [ ] Build API keys page
- [ ] Build billing and usage page
- [ ] Connect frontend to backend API client

## Phase 10: Admin Portal

- [ ] Build admin dashboard
- [ ] Build tenant directory
- [ ] Build tenant detail page
- [ ] Build workspace detail page
- [ ] Build user and membership page
- [ ] Build asset and job explorer
- [ ] Build pipeline diagnostics page
- [ ] Build artifact inspection page
- [ ] Build query and answer audit page
- [ ] Build usage and billing oversight page
- [ ] Build system health dashboard
- [ ] Add admin RBAC guardrails
- [ ] Add support action logging

## Phase 11: SaaS Hardening, Billing, and Governance

- [ ] Implement rate limiting
- [ ] Implement quota enforcement
- [ ] Implement usage metering
- [ ] Implement secure deletion workflow
- [ ] Implement retention policy support
- [ ] Implement export support
- [ ] Implement webhook security
- [ ] Integrate billing provider
- [ ] Map billable units to system events
- [ ] Add tenant isolation verification checks
- [ ] Add secrets management strategy
- [ ] Define PII handling policy

## Phase 12: Reliability, Observability, and Launch Readiness

- [ ] Add structured logs
- [ ] Add traces across API and worker services
- [ ] Add dead-letter queue handling
- [ ] Add failure diagnostics and step telemetry
- [ ] Add reprocessing controls
- [ ] Add artifact integrity checks
- [ ] Add health dashboards
- [ ] Add queue backlog visibility
- [ ] Build modality-based evaluation dataset
- [ ] Measure extraction quality
- [ ] Measure retrieval quality
- [ ] Measure graph correctness
- [ ] Prepare API and SDK docs
- [ ] Prepare onboarding docs
- [ ] Prepare incident response runbook

## Notes

- Update this checklist as implementation progresses.
- Convert partially complete items into more granular subtasks when needed.
- Keep phase status aligned with `PHASE_PLAN.md`.
