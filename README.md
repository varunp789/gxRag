# gxRag Platform

Initial monorepo scaffold for the Graph RAG platform described in [PHASE_PLAN.md](./PHASE_PLAN.md).

## Monorepo layout

- `apps/api`: FastAPI backend
- `apps/worker`: async worker service
- `apps/web`: Next.js App Router frontend
- `libs/core`: shared platform docs and cross-service contracts
- `libs/ui`: shared frontend UI package
- `libs/sdk-ts`: TypeScript SDK
- `libs/sdk-py`: Python SDK
- `infra`: local infrastructure and container setup

## Local setup

### Frontend

1. Install workspace dependencies:

```bash
npm install
```

2. Run the web app:

```bash
npm run dev:web
```

### Backend

1. Create a virtual environment and install editable packages:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e apps/api -e apps/worker -e libs/sdk-py
```

2. Run the API:

```bash
uvicorn app.main:app --reload --app-dir apps/api
```

3. Run the worker:

```bash
python -m worker.main
```

### Infrastructure

Start local dependencies:

```bash
docker compose -f infra/docker-compose.yml up -d
```

## Current status

The compose stack also starts the API and worker. The worker consumes Redis jobs,
with a durable local spool only for development when Redis is unavailable.

## Processing and index configuration

`POST /v1/assets/{asset_id}/process` is asynchronous. Upload requests may include
an optional `content_base64` field; URL assets are fetched by the worker. The
worker stores extracted source evidence under `GXRAG_ARTIFACT_ROOT` and durable
job state under `GXRAG_PROCESSING_STATE_PATH`.

The index writers use pgvector, OpenSearch, ArangoDB, and PostgreSQL. Configure
their URLs in `.env` (see `.env.example`) before processing. Failed backend
writes are retained as failed index records and can be requeued with
`POST /v1/admin/index/reconcile`.

## Current status

The platform now includes:

- monorepo layout
- base FastAPI app
- base Next.js app with client and admin route groups
- provider-backed PDF, spreadsheet, web, image OCR, and hosted audio STT paths
- durable worker queue and resumable processing jobs
- concrete pgvector, OpenSearch, ArangoDB, and PostgreSQL index writers
- shared SDK package skeletons
- Docker Compose for local services
