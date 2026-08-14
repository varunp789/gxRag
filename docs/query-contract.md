# Query Contract

Date: August 13, 2026

## Request Shape

The retrieval APIs should converge on the following request fields:

- `workspace_id`
- `asset_id`
- `query`
- `retrieval_mode`
- `filters`
- `limit`

## Response Shape

The retrieval APIs should converge on the following response fields:

- `results`
- `citations`
- `scores`
- `graph_paths`
- `table_refs`
- `provenance`

## Supported V1 Retrieval Modes

- `vector`
- `hybrid`
- `graph`

`multimodal` remains outside the V1 contract.

