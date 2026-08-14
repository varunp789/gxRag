from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str
    asset_id: str | None = None
    table_id: str | None = None
    limit: int = Field(default=8, ge=1, le=50)
    filters: dict[str, str] = Field(default_factory=dict)


class Citation(BaseModel):
    asset_id: str
    artifact_id: str
    label: str
    provenance: list[str] = Field(default_factory=list)


class RetrievalResult(BaseModel):
    id: str
    kind: str
    content: str
    score: float
    metadata: dict[str, str] = Field(default_factory=dict)
    citation: Citation


class QueryResponse(BaseModel):
    mode: str
    query: str
    results: list[RetrievalResult]
    citations: list[Citation]
    graph_paths: list[list[str]] = Field(default_factory=list)
    table_refs: list[str] = Field(default_factory=list)


class GraphResponse(BaseModel):
    asset_id: str
    entities: list[str]
    relations: list[tuple[str, str]]


class AnswerRequest(QueryRequest):
    model: str = "gpt-4o-mini"


class AnswerResponse(BaseModel):
    id: str
    answer: str
    model: str
    cached: bool
    input_tokens: int
    output_tokens: int
    citations: list[Citation]


class AnswerLog(AnswerResponse):
    workspace_id: str
    mode: str
    created_at: str
