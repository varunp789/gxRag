from __future__ import annotations

import hashlib
from datetime import datetime, timezone

import httpx

from app.core.config import settings
from app.models.retrieval import (
    AnswerLog,
    AnswerRequest,
    AnswerResponse,
    Citation,
    GraphResponse,
    QueryRequest,
    QueryResponse,
    RetrievalResult,
)
from app.services import search
from app.services.asset_registry import ASSETS, _find_asset, seed_assets
from app.services.governance import enforce_quota, record

QUERY_LOGS: list[dict[str, str]] = []
ANSWER_LOGS: list[AnswerLog] = []
ANSWER_CACHE: dict[str, AnswerResponse] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _results(request: QueryRequest, workspace_id: str, mode: str) -> QueryResponse:
    seed_assets()
    assets = [asset for asset in ASSETS if asset.workspace_id == workspace_id]
    if request.asset_id:
        assets = [asset for asset in assets if asset.id == request.asset_id]
    results: list[RetrievalResult] = []
    graph_paths: list[list[str]] = []
    table_refs: list[str] = []
    if mode == "structured":
        for row in search.structured_search(workspace_id, assets, request.query, request.table_id)[:request.limit]:
            citation = Citation(asset_id=row["asset_id"], artifact_id=f"rows:{row['asset_id']}",
                                label=f"row {row['row']}", provenance=row["provenance"])
            table_refs.append(row["asset_id"])
            results.append(RetrievalResult(
                id=f"{row['asset_id']}:row:{row['row']}", kind="structured_row",
                content=" | ".join(f"{key}: {value}" for key, value in row["data"].items()),
                score=row["score"], metadata={k: str(v) for k, v in row["data"].items()}, citation=citation))
    else:
        chunks = search.load_chunks(workspace_id, assets)
        ranked = {
            "vector": search.vector_search,
            "graph": search.graph_search,
        }.get(mode, search.hybrid_search if mode in {"hybrid", "multimodal"} else search.bm25)(chunks, request.query)
        for item in ranked[:request.limit]:
            chunk = item.chunk
            citation = Citation(asset_id=chunk.asset_id, artifact_id=chunk.artifact_id,
                                label=f"chunk {chunk.index}", provenance=chunk.provenance)
            if item.path:
                graph_paths.append(item.path)
            results.append(RetrievalResult(
                id=chunk.chunk_id, kind="chunk", content=chunk.text, score=round(item.score, 6),
                metadata={"asset_type": chunk.asset_type}, citation=citation))
    QUERY_LOGS.append({"workspace_id": workspace_id, "mode": mode, "query": request.query,
                       "created_at": _now(), "result_count": str(len(results))})
    return QueryResponse(mode=mode, query=request.query, results=results,
                         citations=[item.citation for item in results], graph_paths=graph_paths,
                         table_refs=sorted(set(table_refs)))


def query(request: QueryRequest, workspace_id: str, mode: str) -> QueryResponse:
    enforce_quota(workspace_id, "query")
    record(workspace_id, "query")
    return _results(request, workspace_id, mode)


def graph(asset_id: str, workspace_id: str) -> GraphResponse | None:
    seed_assets()
    asset = _find_asset(asset_id)
    if asset is None or asset.workspace_id != workspace_id or asset.status == "deleted":
        return None
    entities, relations = search.graph_for_chunks(search.load_chunks(workspace_id, [asset]))
    return GraphResponse(asset_id=asset_id, entities=entities, relations=relations)


def answer(request: AnswerRequest, workspace_id: str, mode: str) -> AnswerResponse:
    retrieved = query(request, workspace_id, mode)
    if not retrieved.results:
        return AnswerResponse(id="answer_no_evidence", answer="No relevant evidence was found in this workspace.",
                              model=request.model, cached=False, input_tokens=0, output_tokens=0, citations=[])
    cache_key = hashlib.sha256(f"{workspace_id}:{mode}:{request.model}:{request.query}".encode()).hexdigest()
    cached = ANSWER_CACHE.get(cache_key)
    if cached:
        return cached.model_copy(update={"cached": True})
    context = "\n".join(f"[{number}] {result.content}" for number, result in enumerate(retrieved.results, start=1))
    prompt = f"Answer only from this retrieval context and cite sources like [1].\nContext:\n{context}\n\nQuestion: {request.query}"
    if not settings.openai_api_key:
        answer_text = "Hosted answering needs GXRAG_OPENAI_API_KEY. Retrieval evidence is available in the citations."
        output_tokens = 0
    else:
        response = httpx.post("https://api.openai.com/v1/chat/completions", headers={"Authorization": f"Bearer {settings.openai_api_key}"}, json={"model": request.model, "messages": [{"role": "user", "content": prompt}]}, timeout=60)
        response.raise_for_status()
        body = response.json()
        answer_text = body["choices"][0]["message"]["content"]
        output_tokens = body.get("usage", {}).get("completion_tokens", 0)
    result = AnswerResponse(id=f"answer_{cache_key[:12]}", answer=answer_text, model=request.model, cached=False, input_tokens=max(len(prompt.split()), 1), output_tokens=output_tokens, citations=retrieved.citations)
    ANSWER_CACHE[cache_key] = result
    ANSWER_LOGS.append(AnswerLog(**result.model_dump(), workspace_id=workspace_id, mode=mode, created_at=_now()))
    record(workspace_id, "hosted_tokens", result.input_tokens + result.output_tokens)
    return result
