# Retrieval and hosted answers

Use `POST /v1/query/{vector|hybrid|graph|multimodal|structured}` with a `query`, optional `asset_id`, filters, and limit. Responses contain ranked results and per-result citations with source provenance.

The TypeScript and Python SDKs expose matching `vector`, `hybrid`, `graph`, `structured`, and `answer` methods. Hosted answers are available at `POST /v1/answers/{hybrid|graph|multimodal}` and always return the retrieval citations used as evidence.
