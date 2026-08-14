# Asset Registry

Date: August 13, 2026

## Phase 3 Scope Implemented

- Workspace-scoped asset registry
- Asset source and upload records
- Asset version records
- Processing job and job step records
- Artifact registry
- Upload and URL registration endpoints
- Asset list, detail, and status endpoints

## Asset Types in This Scaffold

- `document`
- `spreadsheet`
- `web_page`
- `image`
- `audio`

## Current Limitations

- Registry is in-memory only
- No database migrations yet
- No actual file storage or URL fetching yet
- No background queue yet
- Index records are mocked and not connected to real backends
- Artifact inspection and provenance are scaffolded only
