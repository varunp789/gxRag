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

This is the initial repo foundation:

- monorepo layout
- base FastAPI app
- base Next.js app with client and admin route groups
- worker scaffold
- shared SDK package skeletons
- Docker Compose for local services

