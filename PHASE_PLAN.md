# Graph RAG Platform Phase Plan

## Goal

Build a multi-tenant Graph RAG platform that customers can use as an API-first service or through a hosted web app.

The product should have two distinct application surfaces:

- `Client/User Portal` for customer teams to upload assets, track processing, query knowledge, manage API keys, and consume retrieval results
- `Admin Portal` for internal operators to manage tenants, plans, jobs, pipelines, incidents, billing oversight, support actions, and platform health

Core architecture:

```text
Customer App
    ↓
Your API / SDK
    ↓
Workspace / Tenant Layer
    ↓
Ingestion Pipeline
    ├── PDF
    ├── Image
    ├── Audio
    ├── CSV / Excel
    └── Web content
    ↓
Processing
    ├── Parsing
    ├── OCR / STT
    ├── Chunking
    ├── Embedding
    ├── Entity extraction
    └── Graph construction
    ↓
Indexes
    ├── Vector
    ├── Keyword/BM25
    ├── Graph
    └── Structured data
    ↓
Retrieval API
    ├── Vector
    ├── Hybrid
    ├── Graph
    └── Multimodal
    ↓
Customer's LLM / Your LLM
```

## Product Vision

The platform should let a customer:

1. Create a workspace or tenant
2. Upload or connect content from multiple sources
3. Process that content through a resumable multimodal pipeline
4. Store retrieval-ready outputs in multiple index layers
5. Query the data through API, SDK, or UI
6. Use the retrieval results with either:
   - the customer’s own LLM
   - your hosted LLM orchestration layer

## Platform Outcomes

For each processed asset, the system should return:

- `workspace_id`
- `document_id` or `asset_id`
- `table_id` for structured datasets when applicable
- extraction artifacts
- vector index references
- keyword index references
- graph node and edge references
- queryable metadata and provenance

## Core Product Modules

### 1. Customer Access Layer

- `FastAPI` backend as the public API
- SDKs for customer integration:
  - Python SDK
  - JavaScript/TypeScript SDK
- API key and OAuth support
- Webhooks for job completion and failure notifications

### 1A. Client/User Portal

- customer onboarding
- workspace dashboard
- asset upload and processing status
- graph and table exploration
- retrieval playground
- API key and usage visibility

### 1B. Admin Portal

- tenant and workspace administration
- plan and quota management
- job monitoring and retries
- ingestion pipeline diagnostics
- billing oversight
- support and audit workflows

### 2. Workspace / Tenant Layer

- Tenant isolation
- Workspace-level data boundaries
- role-based access control
- quota enforcement
- usage tracking
- billing hooks

### 3. Ingestion Layer

- Direct file upload
- Batch upload
- URL-based ingestion
- connector-based ingestion in later phases

Supported asset classes:

- PDF
- image
- audio
- CSV / Excel
- web content

### 4. Processing Layer

- format detection
- parsing
- OCR for images and scanned PDFs
- STT for audio
- chunking
- embedding
- entity extraction
- graph construction
- structured table normalization

### 5. Index Layer

- vector index for semantic retrieval
- BM25 or keyword index for lexical retrieval
- graph index for relation and traversal queries
- structured data index for tables, fields, rows, and filters

### 6. Retrieval Layer

- vector retrieval API
- hybrid retrieval API
- graph retrieval API
- multimodal retrieval API
- citations and provenance API

### 7. LLM Consumption Layer

- customer-managed LLM usage through retrieval APIs
- optional hosted answer generation using your own LLM pipeline

## Recommended High-Level Stack

### Backend

- `FastAPI`
- `Pydantic`
- `SQLAlchemy` or `SQLModel`
- `Alembic`

### Workers and Orchestration

- `Celery` or `RQ`
- `Redis`
- step-level retry and resume support

### Storage and Indexing

- `Postgres` for platform metadata
- `pgvector` for embeddings
- `OpenSearch` or `Elasticsearch` for BM25 and keyword search
- `ArangoDB` for graph storage
- object storage for raw files and artifacts

### Frontend

- `Next.js`
- `TypeScript`
- `Tailwind CSS`
- route groups for:
  - client portal
  - admin portal

### Platform

- `Docker`
- CI/CD pipeline
- `Stripe`
- `Sentry`
- `OpenTelemetry`

## Phase 0: Monorepo Foundation and Initial Setup

### Objective

Create the initial monorepo for backend, frontend, workers, SDKs, and shared libraries before feature development starts.

### Monorepo Structure

- `apps/api` for the `FastAPI` backend
- `apps/worker` for ingestion and processing workers
- `apps/web` for the `Next.js` frontend
- `libs/core` for shared domain models, config, constants, and utilities
- `libs/ui` for shared frontend components in later phases
- `libs/sdk-ts` for the TypeScript SDK
- `libs/sdk-py` for the Python SDK
- `infra` for Docker, local services, deployment manifests, and environment setup
- `docs` for architecture, API contracts, and onboarding docs

### Initial Backend Setup

- scaffold `FastAPI` application
- add route versioning pattern
- add health check endpoints
- configure `Pydantic` settings
- configure DB session and migration setup
- add base auth and middleware skeleton

### Initial Frontend Setup

- scaffold `Next.js` app with `TypeScript`
- define route groups for:
  - client portal
  - admin portal
- configure shared layout, auth guards, and API client layer
- add initial design tokens and app shell

### Shared Tooling Setup

- choose monorepo package manager and workspace tool
- configure linting and formatting
- configure type checking
- configure test runners
- configure pre-commit hooks
- configure environment variable management

### DevOps and Local Development Setup

- Docker Compose for local dependencies
- local services for:
  - `Postgres`
  - `Redis`
  - `OpenSearch` or `Elasticsearch`
  - `ArangoDB`
  - object storage emulator if needed
- CI pipeline for lint, test, and build
- environment templates for local, staging, and production

### Deliverables

- working monorepo with backend and frontend apps
- shared library structure
- local development environment
- base CI pipeline
- initial README with setup instructions

### Success Criteria

- A developer can clone the repo and run backend, frontend, and worker locally
- Shared code can be imported cleanly across apps
- CI can validate formatting, linting, and basic builds

## Phase 1: Product and API Definition

### Objective

Define exactly what the platform sells and the contract it exposes.

### Deliverables

- Product packaging:
  - API-only plan
  - hosted app plan
  - enterprise plan
- product surface definition:
  - `Client/User Portal`
  - `Admin Portal`
- usage unit definitions:
  - per file
  - per page
  - per minute of audio
  - per token
  - per query
- V1 source support decision
- V1 retrieval capabilities decision
- admin operations scope decision
- output contract:
  - `workspace_id`
  - `asset_id`
  - `document_id`
  - `table_id`
  - status model
  - artifact model
  - query contract

### API Contract for V1

- `POST /v1/assets/upload`
- `POST /v1/assets/{id}/process`
- `GET /v1/assets/{id}`
- `GET /v1/assets/{id}/status`
- `GET /v1/assets/{id}/artifacts`
- `POST /v1/query/vector`
- `POST /v1/query/hybrid`
- `POST /v1/query/graph`
- `POST /v1/query/multimodal`

### Success Criteria

- Clear V1 scope
- Clear asset model
- Clear retrieval contract
- Clear monetization boundary
- Clear boundary between customer and internal admin capabilities

## Phase 2: Tenant, Workspace, and Access Foundation

### Objective

Create the SaaS foundation before building ingestion complexity.

### Backend Deliverables

- tenant model
- workspace model
- user membership model
- admin user model
- support impersonation policy
- API key model
- role model
- quota model
- audit log model

### Core Database Tables

- `tenants`
- `workspaces`
- `users`
- `workspace_members`
- `admin_users`
- `roles`
- `permissions`
- `api_keys`
- `plans`
- `usage_events`
- `audit_logs`

### Client Portal Deliverables

- sign in flow
- workspace switcher
- tenant settings
- API key management page
- billing placeholder page

### Admin Portal Deliverables

- admin sign in flow
- tenant list page
- tenant detail page
- workspace inspection page
- user and role management page
- plan and quota controls
- audit log viewer

### Success Criteria

- Every asset belongs to a workspace
- Every query is workspace-scoped
- Access control is enforced before ingestion work begins
- Admin and client permissions are clearly separated

## Phase 3: Unified Asset Registry and Ingestion Entry

### Objective

Introduce a normalized asset model that supports many content types.

### Asset Types

- `document`
- `image`
- `audio`
- `spreadsheet`
- `web_page`

### Database Tables

- `assets`
- `asset_versions`
- `asset_sources`
- `asset_uploads`
- `processing_jobs`
- `job_steps`
- `artifacts`

### FastAPI Endpoints

- `POST /v1/assets/upload`
- `POST /v1/assets/from-url`
- `POST /v1/assets/{id}/process`
- `GET /v1/assets`
- `GET /v1/assets/{id}`
- `GET /v1/assets/{id}/status`

### Client Portal Deliverables

- upload page
- source type selector
- asset list page
- asset detail page
- processing timeline

### Admin Portal Deliverables

- global asset search
- stuck job review page
- failed upload inspection page
- tenant-level asset activity view

### Success Criteria

- Assets can be created from upload or URL
- Asset metadata is normalized across types
- Jobs are tracked consistently for all content types
- Internal teams can inspect asset lifecycle without direct database access

## Phase 4: Multi-Format Ingestion Pipeline

### Objective

Support source-specific ingestion while preserving a shared downstream processing contract.

### Ingestion Adapters

#### PDF Adapter

- detect native text vs scanned pages
- extract pages, text, and tables
- store page-level metadata

#### Image Adapter

- detect image type
- OCR text
- extract layout regions if needed

#### Audio Adapter

- speech-to-text
- speaker segmentation in later phase
- timestamped transcript creation

#### CSV / Excel Adapter

- parse sheets
- infer headers, column types, and row structure
- register tables and field metadata

#### Web Content Adapter

- fetch HTML
- sanitize content
- extract main text, headings, links, and metadata

### Shared Artifact Contract

Every adapter should produce:

- normalized raw content
- source metadata
- page, row, segment, or timestamp references
- extraction warnings

### Success Criteria

- Each supported source type can enter the same downstream processing pipeline
- Source-specific complexity is isolated in adapters
- Artifacts are consistent enough for common processing steps
- Admin operators can inspect ingestion failures by adapter and source type

## Phase 5: Processing Pipeline

### Objective

Build a resumable processing pipeline that converts raw content into retrieval-ready knowledge.

### Processing Stages

#### 1. Inspect and Plan

- identify asset type and domain hints
- decide extraction strategy
- define section or segment plan

Outputs:

- `plan.json`

#### 2. Parse / OCR / STT

- text extraction for documents
- OCR for scanned pages and images
- STT for audio
- row and schema extraction for spreadsheets

Outputs:

- `raw_extracted.md`
- transcript artifacts
- structured table artifacts

#### 3. Normalize and Structure

- unify text structure
- preserve provenance references
- create section, page, row, and timestamp mappings

Outputs:

- normalized content artifacts
- content map metadata

#### 4. Chunking

- create chunk boundaries by modality and structure
- preserve parent-child relationships
- assign stable chunk IDs

Outputs:

- `chunks`
- `chunk_groups`

#### 5. Embedding

- generate embeddings for text and supported multimodal representations

Outputs:

- vector rows

#### 6. Entity and Relation Extraction

- extract entities from text, tables, and metadata
- infer relationships
- link all extractions to evidence

Outputs:

- `entities`
- `relations`

#### 7. Graph Construction

- convert extracted knowledge into graph nodes and edges
- store graph-ready provenance links

Outputs:

- graph vertices
- graph edges

#### 8. Structured Data Registration

- register tables, schemas, fields, and row references
- enable structured filtering and table retrieval

Outputs:

- `tables`
- `table_columns`
- `table_rows`

### Pipeline Requirements

- idempotent steps
- resumable execution
- retry per step
- artifact versioning
- provenance preservation

### Admin Portal Deliverables

- job queue monitor
- step-by-step job detail page
- retry failed step action
- reprocess asset action
- artifact inspection page

### Success Criteria

- A single orchestration model works across formats
- Assets can resume after failure
- All extracted data remains traceable to source evidence
- Support team can operate the pipeline without manual shell access

## Phase 6: Index Layer Implementation

### Objective

Materialize all retrieval backends required by the architecture.

### Index Types

#### Vector Index

- chunk embeddings
- table cell or row embeddings where needed
- optional image or multimodal embeddings in later stages

#### Keyword / BM25 Index

- chunk text
- document titles
- metadata fields
- table captions and headers

#### Graph Index

- entities
- relations
- graph neighborhoods
- traversal-ready edges

#### Structured Data Index

- table registry
- schema metadata
- row filters
- column filters

### Storage Mapping

- `Postgres`: control plane and structured metadata
- `pgvector`: semantic vectors
- `OpenSearch` or `Elasticsearch`: BM25 and hybrid lexical support
- `ArangoDB`: graph model

### Success Criteria

- Every processed asset can populate one or more index layers
- Retrieval can combine multiple indexes by workspace and asset
- Structured datasets are queryable alongside text and graph data
- Admin users can inspect index population status and failures

## Phase 7: Retrieval API and SDK Layer

### Objective

Expose index capabilities through clean customer-facing APIs and SDKs.

### Retrieval Endpoints

- `POST /v1/query/vector`
- `POST /v1/query/hybrid`
- `POST /v1/query/graph`
- `POST /v1/query/multimodal`
- `POST /v1/query/structured`
- `GET /v1/assets/{id}/graph`
- `GET /v1/assets/{id}/entities`
- `GET /v1/assets/{id}/relations`
- `GET /v1/tables/{table_id}`

### Request Inputs

- `workspace_id`
- `asset_id`
- `document_id`
- `table_id`
- query text
- modality hints
- filters by type, date, page, row, timestamp, entity class

### Response Contract

- ranked results
- chunks or rows
- graph paths
- table references
- provenance
- scores
- citations

### SDK Deliverables

- Python SDK
- TypeScript SDK
- example notebook
- example Next.js integration

### Client Portal Deliverables

- retrieval playground
- graph query UI
- structured query UI
- results viewer with citations

### Admin Portal Deliverables

- query log explorer
- workspace retrieval usage view
- slow query diagnostics view

### Success Criteria

- Customers can integrate without using your UI
- SDKs map directly to API contracts
- Retrieval outputs are usable for downstream LLM prompting
- Internal teams can debug retrieval behavior per workspace

## Phase 8: LLM Integration Layer

### Objective

Support both BYO-LLM and hosted answer generation.

### Mode A: Customer LLM

- retrieval-only mode
- customer receives chunks, graph results, and citations
- customer handles prompt composition and answer generation

### Mode B: Hosted LLM

- your platform performs retrieval orchestration
- your platform generates final answers
- responses include citations and evidence paths

### Hosted Endpoints

- `POST /v1/answers/hybrid`
- `POST /v1/answers/graph`
- `POST /v1/answers/multimodal`

### Platform Requirements

- model abstraction layer
- prompt templates
- token metering
- answer logging
- optional response caching

### Client Portal Deliverables

- hosted answer playground
- answer history page
- citation and evidence viewer

### Admin Portal Deliverables

- hosted answer audit page
- token consumption view
- model and prompt diagnostics page

### Success Criteria

- Customers can choose retrieval-only or answer-generation modes
- LLM usage can be tracked and billed separately
- Hosted answers remain grounded in retrievable evidence

## Phase 9: Next.js Client/User Portal

### Objective

Build a hosted product experience around the API platform.

### Pages

- landing page
- sign in and onboarding
- workspace dashboard
- asset upload page
- asset detail page
- processing timeline page
- graph explorer
- structured table explorer
- retrieval playground
- API keys page
- billing and usage page

### Key UI Components

- upload zone
- source-type selector
- asset status timeline
- artifact preview panel
- graph visualization
- chunk inspector
- table inspector
- query console
- citations panel

### V1 UX Priorities

- Upload any supported asset from one entry point
- Show pipeline progress clearly
- Expose `asset_id`, `document_id`, and `table_id`
- Let users test vector, hybrid, and graph retrieval quickly

### Success Criteria

- A customer can onboard, upload, process, inspect, and query without API knowledge
- UI maps directly to backend capability
- Hosted app and SDK remain consistent

## Phase 10: Admin Portal

### Objective

Build an internal operations portal for platform management, customer support, and pipeline observability.

### Pages

- admin sign in
- tenant directory
- tenant detail and plan page
- workspace detail page
- user and membership page
- asset and job explorer
- pipeline diagnostics page
- artifact inspection page
- query and answer audit page
- usage and billing oversight page
- system health dashboard

### Key UI Components

- tenant search
- workspace switch context panel
- job retry controls
- support action drawer
- audit trail viewer
- cost and usage charts
- incident status widgets

### Guardrails

- strict admin RBAC
- support action logging
- read-only vs write-action separation
- impersonation controls with audit trail

### Success Criteria

- Support and ops can manage customers without direct DB access
- Every sensitive admin action is logged
- Admin workflows reduce operational load during beta and production

## Phase 11: SaaS Hardening, Billing, and Governance

### Objective

Prepare the platform for real customer workloads.

### Required Capabilities

- rate limiting
- quota enforcement
- usage metering
- secure deletion
- retention policies
- export support
- audit trails
- webhook security

### Billing Dimensions

- files processed
- pages processed
- minutes of audio processed
- embedding usage
- retrieval request count
- hosted LLM token usage

### Security and Compliance

- tenant isolation checks
- encrypted storage
- secrets management
- PII handling policy
- admin access boundaries

### Success Criteria

- Usage is measurable and enforceable
- Costs map to billable units
- Security boundaries are testable

## Phase 12: Reliability, Observability, and Launch Readiness

### Objective

Make the platform supportable in production.

### Operational Features

- structured logs
- traces across API and workers
- retry policies
- dead-letter queue
- step diagnostics
- reprocessing controls
- artifact integrity checks
- health checks

### Admin Portal Requirements

- real-time job health widgets
- failed pipeline alerts
- queue backlog visibility
- service dependency status
- incident annotation support

### Quality Evaluation

- gold dataset per modality
- extraction accuracy checks
- OCR quality checks
- STT quality checks
- retrieval relevance benchmarks
- graph correctness checks
- grounding evaluation for hosted answers

### Launch Deliverables

- API docs
- SDK docs
- architecture diagram
- onboarding guide
- pricing page
- incident response runbook

### Success Criteria

- Platform failures are diagnosable
- Retrieval quality is measurable
- Beta launch can happen with known operational guardrails

## Suggested Delivery Sequence

### Milestone 1

- Phase 0
- Phase 1
- Phase 2

Result:

- Monorepo setup, product definition, and multi-tenant foundation

### Milestone 2

- Phase 3
- Phase 4

Result:

- Asset registry and multi-format ingestion pipeline

### Milestone 3

- Phase 5
- Phase 6

Result:

- Unified processing pipeline and index layer

### Milestone 4

- Phase 7
- Phase 8
- Phase 9

Result:

- Retrieval platform, SDKs, hosted answer generation, and client portal

### Milestone 5

- Phase 10
- Phase 11

Result:

- Admin portal plus SaaS hardening and governance

### Milestone 6

- Phase 12

Result:

- Reliable, observable, launch-ready SaaS platform

## Recommended V1 Scope

To keep the first version realistic, narrow scope as follows:

- support `PDF`, `CSV`, and basic `web content` first
- make `image` and `audio` phase 2 capabilities unless required immediately
- start with vector plus BM25 plus graph retrieval
- keep multimodal answer generation behind a later feature flag
- launch retrieval-first before fully managed hosted answer generation

## Immediate Next Build Steps

1. Create monorepo structure:
   - `apps/api`
   - `apps/worker`
   - `apps/web`
   - `libs/core`
   - `libs/ui`
   - `libs/sdk-ts`
   - `libs/sdk-py`
   - `infra`
2. Set up workspace tooling, linting, testing, and CI
3. Bootstrap `FastAPI`, `Next.js`, and worker entrypoints
4. Add local Docker services for core dependencies
5. Design the workspace, asset, and job schema
6. Implement upload and processing job APIs
7. Build the adapter interface for PDF, CSV, and web ingestion
