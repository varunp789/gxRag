# API Scope

Date: August 13, 2026

## Phase 1 API Surface

### Platform metadata

- `GET /v1/platform/definition`
- `GET /v1/platform/api-scope`

### Access foundation

- `GET /v1/access/overview`
- `GET /v1/workspaces`
- `GET /v1/workspaces/current`
- `GET /v1/admin/tenants`
- `GET /v1/admin/tenants/{tenant_id}`
- `GET /v1/admin/workspaces/{workspace_id}`

### Asset registry and ingestion

- `GET /v1/assets`
- `POST /v1/assets/upload`
- `POST /v1/assets/from-url`
- `GET /v1/assets/{asset_id}`
- `GET /v1/assets/{asset_id}/status`
- `POST /v1/assets/{asset_id}/process`
- `GET /v1/admin/assets`
- `GET /v1/admin/ingestion/diagnostics`

## Authentication and Scoping Stub

Current implementation uses request headers as a development scaffold:

- `X-Actor-Email` for workspace users
- `X-Admin-Email` for admin users
- `X-Workspace-Id` to choose the active workspace

These headers are temporary until real auth is implemented.

## Planned Next API Surface

The next implementation phase should add:

- database-backed asset persistence
- background workers for ingestion processing
- real upload storage and URL fetching
- artifact retrieval and preview endpoints
