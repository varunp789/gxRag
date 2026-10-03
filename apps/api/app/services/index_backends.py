"""Concrete index writers for pgvector, OpenSearch, ArangoDB and PostgreSQL.

Each writer performs a real backend write.  Failures are returned to the
pipeline as diagnostics so the reconciliation job can retry them later.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

import httpx
import psycopg

from app.core.config import settings


@dataclass(frozen=True)
class IndexWriteResult:
    index_type: str
    backend: str
    document_count: int
    external_id: str


def deterministic_embedding(text: str, dimensions: int = 16) -> list[float]:
    """A deterministic development embedding until a configured model is used."""
    digest = hashlib.sha512(text.encode("utf-8")).digest()
    return [round((digest[index] / 127.5) - 1, 6) for index in range(dimensions)]


def write_vector(*, workspace_id: str, asset_id: str, chunks: list[str]) -> IndexWriteResult:
    with psycopg.connect(settings.vector_database_url, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS gxrag_vectors (
                    workspace_id text NOT NULL, asset_id text NOT NULL,
                    chunk_id text NOT NULL, content text NOT NULL,
                    embedding vector(16) NOT NULL,
                    PRIMARY KEY (workspace_id, asset_id, chunk_id))"""
            )
            for position, chunk in enumerate(chunks):
                cursor.execute(
                    """INSERT INTO gxrag_vectors
                    (workspace_id, asset_id, chunk_id, content, embedding)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (workspace_id, asset_id, chunk_id) DO UPDATE
                    SET content = EXCLUDED.content, embedding = EXCLUDED.embedding""",
                    (workspace_id, asset_id, str(position), chunk, deterministic_embedding(chunk)),
                )
    return IndexWriteResult("vector", "pgvector", len(chunks), f"{workspace_id}:{asset_id}")


def write_keyword(*, workspace_id: str, asset_id: str, title: str, chunks: list[str]) -> IndexWriteResult:
    index_name = "gxrag-chunks"
    operations = []
    for position, chunk in enumerate(chunks):
        operations.extend([
            json.dumps({"index": {"_index": index_name, "_id": f"{workspace_id}:{asset_id}:{position}"}}),
            json.dumps({"workspace_id": workspace_id, "asset_id": asset_id, "title": title, "content": chunk}),
        ])
    response = httpx.post(
        f"{settings.opensearch_url.rstrip('/')}/_bulk",
        content="\n".join(operations) + "\n",
        headers={"Content-Type": "application/x-ndjson"}, timeout=5,
    )
    response.raise_for_status()
    if response.json().get("errors"):
        raise RuntimeError("OpenSearch rejected one or more index documents.")
    return IndexWriteResult("keyword", "opensearch", len(chunks), f"{index_name}:{asset_id}")


def _arango_request(method: str, path: str, payload: dict | None = None) -> httpx.Response:
    return httpx.request(
        method, f"{settings.arangodb_url.rstrip('/')}{path}", json=payload,
        auth=(settings.arangodb_username, settings.arangodb_password), timeout=5,
    )


def _entity_key(workspace_id: str, asset_id: str, entity: str) -> str:
    return hashlib.sha1(f"{workspace_id}:{asset_id}:{entity}".encode()).hexdigest()


def write_graph(*, workspace_id: str, asset_id: str, entities: list[str], relations: list[tuple[str, str]]) -> IndexWriteResult:
    database = settings.arangodb_database
    _arango_request("POST", "/_api/database", {"name": database})
    vertices, edges = "gxrag_entities", "gxrag_relations"
    for name, collection_type in ((vertices, 2), (edges, 3)):  # 2 = document, 3 = edge
        response = _arango_request("POST", f"/_db/{database}/_api/collection", {"name": name, "type": collection_type})
        if response.status_code not in {200, 201, 202, 409}:
            response.raise_for_status()
    for entity in entities:
        response = _arango_request("POST", f"/_db/{database}/_api/document/{vertices}", {
            "_key": _entity_key(workspace_id, asset_id, entity), "workspace_id": workspace_id,
            "asset_id": asset_id, "label": entity,
        })
        if response.status_code not in {201, 202, 409}:
            response.raise_for_status()
    known = set(entities)
    for left, right in relations:
        if left not in known or right not in known:
            continue
        response = _arango_request("POST", f"/_db/{database}/_api/document/{edges}", {
            "_key": hashlib.sha1(f"{workspace_id}:{asset_id}:{left}->{right}".encode()).hexdigest(),
            "_from": f"{vertices}/{_entity_key(workspace_id, asset_id, left)}",
            "_to": f"{vertices}/{_entity_key(workspace_id, asset_id, right)}",
            "workspace_id": workspace_id, "asset_id": asset_id,
        })
        if response.status_code not in {201, 202, 409}:
            response.raise_for_status()
    return IndexWriteResult("graph", "arangodb", len(entities) + len(relations), f"{vertices}:{asset_id}")


def write_structured(*, workspace_id: str, asset_id: str, rows: list[dict[str, str]]) -> IndexWriteResult:
    with psycopg.connect(settings.vector_database_url, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS gxrag_structured_rows (
                    workspace_id text NOT NULL, asset_id text NOT NULL,
                    row_number integer NOT NULL, data jsonb NOT NULL,
                    PRIMARY KEY (workspace_id, asset_id, row_number))"""
            )
            for position, row in enumerate(rows):
                cursor.execute(
                    """INSERT INTO gxrag_structured_rows (workspace_id, asset_id, row_number, data)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (workspace_id, asset_id, row_number) DO UPDATE SET data = EXCLUDED.data""",
                    (workspace_id, asset_id, position, json.dumps(row)),
                )
    return IndexWriteResult("structured", "postgres", len(rows), f"{workspace_id}:{asset_id}")
