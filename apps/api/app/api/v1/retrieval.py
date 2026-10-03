from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies.access import WorkspaceAccess, require_admin, require_permission
from app.models.access import AdminUser, Workspace
from app.models.retrieval import AnswerLog, AnswerRequest, AnswerResponse, GraphResponse, QueryRequest, QueryResponse
from app.services.retrieval import ANSWER_LOGS, QUERY_LOGS, answer, graph, query

router = APIRouter()

def _query(mode: str, payload: QueryRequest, workspace: Workspace) -> QueryResponse:
    return query(payload, workspace.id, mode)

@router.post("/query/vector", response_model=QueryResponse, tags=["query"])
def vector(payload: QueryRequest, access: Annotated[WorkspaceAccess, Depends(require_permission("query.run"))]): return _query("vector", payload, access.workspace)
@router.post("/query/hybrid", response_model=QueryResponse, tags=["query"])
def hybrid(payload: QueryRequest, access: Annotated[WorkspaceAccess, Depends(require_permission("query.run"))]): return _query("hybrid", payload, access.workspace)
@router.post("/query/graph", response_model=QueryResponse, tags=["query"])
def graph_query(payload: QueryRequest, access: Annotated[WorkspaceAccess, Depends(require_permission("query.run"))]): return _query("graph", payload, access.workspace)
@router.post("/query/multimodal", response_model=QueryResponse, tags=["query"])
def multimodal(payload: QueryRequest, access: Annotated[WorkspaceAccess, Depends(require_permission("query.run"))]): return _query("multimodal", payload, access.workspace)
@router.post("/query/structured", response_model=QueryResponse, tags=["query"])
def structured(payload: QueryRequest, access: Annotated[WorkspaceAccess, Depends(require_permission("query.run"))]): return _query("structured", payload, access.workspace)
@router.get("/assets/{asset_id}/graph", response_model=GraphResponse, tags=["query"])
def asset_graph(asset_id: str, access: Annotated[WorkspaceAccess, Depends(require_permission("assets.read"))]):
    result = graph(asset_id, access.workspace.id)
    if not result: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found.")
    return result
@router.get("/assets/{asset_id}/entities", response_model=list[str], tags=["query"])
def entities(asset_id: str, access: Annotated[WorkspaceAccess, Depends(require_permission("assets.read"))]): return asset_graph(asset_id, access).entities
@router.get("/assets/{asset_id}/relations", response_model=list[tuple[str, str]], tags=["query"])
def relations(asset_id: str, access: Annotated[WorkspaceAccess, Depends(require_permission("assets.read"))]): return asset_graph(asset_id, access).relations
@router.get("/tables/{table_id}", tags=["query"])
def table(table_id: str, access: Annotated[WorkspaceAccess, Depends(require_permission("query.run"))]):
    response = query(QueryRequest(query=table_id, table_id=table_id), access.workspace.id, "structured")
    return {"table_id": table_id, "workspace_id": access.workspace.id, "rows": response.results, "citations": response.citations}
@router.post("/answers/{mode}", response_model=AnswerResponse, tags=["answers"])
def hosted_answer(mode: str, payload: AnswerRequest, access: Annotated[WorkspaceAccess, Depends(require_permission("query.run"))]):
    if mode not in {"hybrid", "graph", "multimodal"}: raise HTTPException(status_code=404, detail="Unsupported answer mode.")
    return answer(payload, access.workspace.id, mode)
@router.get("/admin/query-logs", tags=["admin"])
def query_logs(_: Annotated[AdminUser, Depends(require_admin("admin.support"))]): return list(reversed(QUERY_LOGS))
@router.get("/admin/answer-logs", response_model=list[AnswerLog], tags=["admin"])
def answer_logs(_: Annotated[AdminUser, Depends(require_admin("admin.support"))]): return list(reversed(ANSWER_LOGS))
