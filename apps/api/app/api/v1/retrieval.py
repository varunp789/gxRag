from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies.access import get_current_admin, get_current_workspace
from app.models.access import AdminUser, Workspace
from app.models.retrieval import AnswerLog, AnswerRequest, AnswerResponse, GraphResponse, QueryRequest, QueryResponse
from app.services.retrieval import ANSWER_LOGS, QUERY_LOGS, answer, graph, query

router = APIRouter()

def _query(mode: str, payload: QueryRequest, workspace: Workspace) -> QueryResponse:
    return query(payload, workspace.id, mode)

@router.post("/query/vector", response_model=QueryResponse, tags=["query"])
def vector(payload: QueryRequest, workspace: Annotated[Workspace, Depends(get_current_workspace)]): return _query("vector", payload, workspace)
@router.post("/query/hybrid", response_model=QueryResponse, tags=["query"])
def hybrid(payload: QueryRequest, workspace: Annotated[Workspace, Depends(get_current_workspace)]): return _query("hybrid", payload, workspace)
@router.post("/query/graph", response_model=QueryResponse, tags=["query"])
def graph_query(payload: QueryRequest, workspace: Annotated[Workspace, Depends(get_current_workspace)]): return _query("graph", payload, workspace)
@router.post("/query/multimodal", response_model=QueryResponse, tags=["query"])
def multimodal(payload: QueryRequest, workspace: Annotated[Workspace, Depends(get_current_workspace)]): return _query("multimodal", payload, workspace)
@router.post("/query/structured", response_model=QueryResponse, tags=["query"])
def structured(payload: QueryRequest, workspace: Annotated[Workspace, Depends(get_current_workspace)]): return _query("structured", payload, workspace)
@router.get("/assets/{asset_id}/graph", response_model=GraphResponse, tags=["query"])
def asset_graph(asset_id: str, workspace: Annotated[Workspace, Depends(get_current_workspace)]):
    result = graph(asset_id, workspace.id)
    if not result: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found.")
    return result
@router.get("/assets/{asset_id}/entities", response_model=list[str], tags=["query"])
def entities(asset_id: str, workspace: Annotated[Workspace, Depends(get_current_workspace)]): return asset_graph(asset_id, workspace).entities
@router.get("/assets/{asset_id}/relations", response_model=list[tuple[str, str]], tags=["query"])
def relations(asset_id: str, workspace: Annotated[Workspace, Depends(get_current_workspace)]): return asset_graph(asset_id, workspace).relations
@router.get("/tables/{table_id}", tags=["query"])
def table(table_id: str, workspace: Annotated[Workspace, Depends(get_current_workspace)]):
    response = query(QueryRequest(query=table_id, table_id=table_id), workspace.id, "structured")
    return {"table_id": table_id, "workspace_id": workspace.id, "rows": response.results, "citations": response.citations}
@router.post("/answers/{mode}", response_model=AnswerResponse, tags=["answers"])
def hosted_answer(mode: str, payload: AnswerRequest, workspace: Annotated[Workspace, Depends(get_current_workspace)]):
    if mode not in {"hybrid", "graph", "multimodal"}: raise HTTPException(status_code=404, detail="Unsupported answer mode.")
    return answer(payload, workspace.id, mode)
@router.get("/admin/query-logs", tags=["admin"])
def query_logs(_: Annotated[AdminUser, Depends(get_current_admin)]): return list(reversed(QUERY_LOGS))
@router.get("/admin/answer-logs", response_model=list[AnswerLog], tags=["admin"])
def answer_logs(_: Annotated[AdminUser, Depends(get_current_admin)]): return list(reversed(ANSWER_LOGS))
