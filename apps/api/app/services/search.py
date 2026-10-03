"""Local retrieval engine over extracted artifacts.

Implements the five query modes against the content the pipeline extracted so
retrieval works (and can be evaluated) without external search clusters:

* keyword/BM25 -- term statistics per workspace
* vector      -- cosine similarity of hashed character-trigram vectors
* hybrid      -- reciprocal-rank fusion of BM25 and vector
* graph       -- entity co-occurrence expansion with explicit paths
* structured  -- row filtering over extracted tables
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path

from app.core.config import settings
from app.services.text import chunk_text, extract_entities, extract_relations, tokenize

VECTOR_DIMENSIONS = 1024


@dataclass
class Chunk:
    asset_id: str
    artifact_id: str
    index: int
    text: str
    provenance: list[str] = field(default_factory=list)
    asset_type: str = ""
    tokens: list[str] = field(default_factory=list)

    @property
    def chunk_id(self) -> str:
        return f"{self.asset_id}:chunk:{self.index}"


@dataclass
class Scored:
    chunk: Chunk
    score: float
    path: list[str] = field(default_factory=list)


def trigram_vector(text: str) -> list[float]:
    vector = [0.0] * VECTOR_DIMENSIONS
    normalized = f"  {' '.join(tokenize(text))}  "
    for position in range(len(normalized) - 2):
        digest = hashlib.md5(normalized[position:position + 3].encode(), usedforsecurity=False).digest()
        vector[int.from_bytes(digest[:2], "big") % VECTOR_DIMENSIONS] += 1.0
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def _cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def latest_artifact_dir(workspace_id: str, asset_id: str) -> Path | None:
    root = Path(settings.artifact_root) / workspace_id / asset_id
    versions = sorted(
        (path for path in root.glob("v*") if path.is_dir() and path.name[1:].isdigit()),
        key=lambda path: int(path.name[1:]),
    ) if root.exists() else []
    return versions[-1] if versions else None


def load_chunks(workspace_id: str, assets: list) -> list[Chunk]:
    """Chunks for the workspace's non-deleted assets (``assets`` are Asset models)."""
    chunks: list[Chunk] = []
    for asset in assets:
        if asset.workspace_id != workspace_id or asset.status in {"deleted", "failed"}:
            continue
        directory = latest_artifact_dir(workspace_id, asset.id)
        if directory is None or not (directory / "raw_extracted.md").exists():
            continue
        text = (directory / "raw_extracted.md").read_text(errors="replace")
        for index, piece in enumerate(chunk_text(text)):
            chunks.append(Chunk(
                asset_id=asset.id, artifact_id=f"raw:{asset.id}:{directory.name}", index=index, text=piece,
                provenance=[f"asset:{asset.id}", f"workspace:{workspace_id}", f"version:{directory.name}"],
                asset_type=asset.asset_type, tokens=tokenize(piece),
            ))
    return chunks


def bm25(chunks: list[Chunk], query: str, k1: float = 1.5, b: float = 0.75) -> list[Scored]:
    terms = tokenize(query)
    if not terms or not chunks:
        return []
    average = sum(len(chunk.tokens) for chunk in chunks) / len(chunks) or 1.0
    document_frequency = {term: sum(term in set(chunk.tokens) for chunk in chunks) for term in set(terms)}
    scored: list[Scored] = []
    for chunk in chunks:
        score = 0.0
        for term in set(terms):
            frequency = chunk.tokens.count(term)
            if not frequency:
                continue
            idf = math.log(1 + (len(chunks) - document_frequency[term] + 0.5) / (document_frequency[term] + 0.5))
            score += idf * frequency * (k1 + 1) / (frequency + k1 * (1 - b + b * len(chunk.tokens) / average))
        if score > 0:
            scored.append(Scored(chunk, score))
    return sorted(scored, key=lambda item: (-item.score, item.chunk.chunk_id))


def vector_search(chunks: list[Chunk], query: str) -> list[Scored]:
    query_vector = trigram_vector(query)
    scored = [Scored(chunk, _cosine(query_vector, trigram_vector(chunk.text))) for chunk in chunks]
    return sorted((item for item in scored if item.score > 0.2), key=lambda item: (-item.score, item.chunk.chunk_id))


def hybrid_search(chunks: list[Chunk], query: str, k: int = 60) -> list[Scored]:
    fused: dict[str, float] = {}
    by_id: dict[str, Chunk] = {}
    for ranking in (bm25(chunks, query), vector_search(chunks, query)):
        for rank, item in enumerate(ranking, start=1):
            fused[item.chunk.chunk_id] = fused.get(item.chunk.chunk_id, 0.0) + 1.0 / (k + rank)
            by_id[item.chunk.chunk_id] = item.chunk
    return sorted((Scored(by_id[key], value) for key, value in fused.items()),
                  key=lambda item: (-item.score, item.chunk.chunk_id))


def graph_search(chunks: list[Chunk], query: str) -> list[Scored]:
    """Seed with BM25 hits, then expand through entities shared with other chunks."""
    seeds = bm25(chunks, query)[:3]
    if not seeds:
        return []
    entities = extract_entities(" ".join(chunk.text for chunk in chunks), limit=500)
    results: dict[str, Scored] = {item.chunk.chunk_id: item for item in seeds}
    for seed in seeds:
        seed_entities = [entity for entity in entities if entity in seed.chunk.text]
        for other in chunks:
            if other.chunk_id in results:
                continue
            shared = [entity for entity in seed_entities if entity in other.text]
            if shared:
                results[other.chunk_id] = Scored(
                    other, seed.score * 0.5 * len(shared) / max(len(seed_entities), 1),
                    path=[seed.chunk.chunk_id, shared[0], other.chunk_id])
    return sorted(results.values(), key=lambda item: (-item.score, item.chunk.chunk_id))


def graph_for_chunks(chunks: list[Chunk]) -> tuple[list[str], list[tuple[str, str]]]:
    texts = [chunk.text for chunk in chunks]
    entities = extract_entities(" ".join(texts))
    return entities, extract_relations(texts, entities)


def structured_search(workspace_id: str, assets: list, query: str, table_id: str | None = None) -> list[dict]:
    """Rows from extracted spreadsheets ranked by matching terms."""
    terms = set(tokenize(query))
    rows: list[dict] = []
    for asset in assets:
        if asset.workspace_id != workspace_id or asset.status in {"deleted", "failed"}:
            continue
        if table_id and table_id not in {asset.id, f"table_{asset.id}"}:
            continue
        directory = latest_artifact_dir(workspace_id, asset.id)
        if directory is None or not (directory / "structured_rows.json").exists():
            continue
        for number, row in enumerate(json.loads((directory / "structured_rows.json").read_text()), start=1):
            haystack = set(tokenize(" ".join(str(value) for value in row.values())))
            overlap = len(terms & haystack)
            if overlap or table_id:
                rows.append({"asset_id": asset.id, "row": number, "score": overlap / max(len(terms), 1),
                             "data": row, "provenance": [f"asset:{asset.id}", f"row:{number}"]})
    return sorted(rows, key=lambda item: (-item["score"], item["asset_id"], item["row"]))
