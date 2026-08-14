# Product Definition

Date: August 13, 2026

## V1 Product Packaging

- `API Starter`
  - For customers embedding retrieval into their own application
  - Billing model: documents processed plus queries executed
- `Hosted Workspace`
  - For customers using the client portal and managed retrieval
  - Billing model: workspace subscription plus usage
- `Enterprise`
  - For customers requiring governance, support workflows, and extended admin controls
  - Billing model: contracted capacity

## V1 Source Types

- Enabled:
  - PDF
  - CSV / Excel
  - Web content
- Deferred:
  - Image
  - Audio

## V1 Retrieval Modes

- Enabled:
  - Vector retrieval
  - Hybrid retrieval
  - Graph retrieval
- Deferred:
  - Multimodal retrieval

## Admin Operations Scope

- Tenant and workspace administration
- Plan and quota oversight
- Audit and support workflows
- Preparation for job monitoring and retries in the next phase

## Canonical Asset Output Contract

Each processed asset should ultimately expose:

- `workspace_id`
- `asset_id`
- `document_id`
- `table_id`
- `artifact_refs`
- `graph_refs`
- `vector_index_refs`
- `keyword_index_refs`
- `provenance`

## Versioning Policy

- Public APIs live under `/v1`
- Additive changes are allowed within `v1`
- Breaking changes require a new major version such as `/v2`

