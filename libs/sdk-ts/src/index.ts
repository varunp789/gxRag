export type QueryMode = "vector" | "hybrid" | "graph" | "multimodal" | "structured";
export type QueryRequest = { query: string; asset_id?: string; table_id?: string; limit?: number; filters?: Record<string, string> };
export type Citation = { asset_id: string; artifact_id: string; label: string; provenance: string[] };
export type QueryResponse = { mode: QueryMode; query: string; results: Array<{ id: string; kind: string; content: string; score: number; citation: Citation }>; citations: Citation[]; graph_paths: string[][]; table_refs: string[] };
export type AnswerResponse = { id: string; answer: string; model: string; cached: boolean; input_tokens: number; output_tokens: number; citations: Citation[] };

export class GXRagClient {
  constructor(private readonly baseUrl: string, private readonly workspaceId?: string) {}
  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl.replace(/\/$/, "")}/v1${path}`, { ...init, headers: { Accept: "application/json", ...(this.workspaceId ? { "X-Workspace-Id": this.workspaceId } : {}), ...init?.headers } });
    if (!response.ok) throw new Error(`gxRag request failed: ${response.status}`);
    return response.json() as Promise<T>;
  }
  health() { return this.request<{ status: string; service: string; timestamp: string }>("/health"); }
  query(mode: QueryMode, request: QueryRequest) { return this.request<QueryResponse>(`/query/${mode}`, { method: "POST", body: JSON.stringify(request), headers: { "Content-Type": "application/json" } }); }
  vector(request: QueryRequest) { return this.query("vector", request); }
  hybrid(request: QueryRequest) { return this.query("hybrid", request); }
  graph(request: QueryRequest) { return this.query("graph", request); }
  structured(request: QueryRequest) { return this.query("structured", request); }
  answer(mode: "hybrid" | "graph" | "multimodal", request: QueryRequest & { model?: string }) { return this.request<AnswerResponse>(`/answers/${mode}`, { method: "POST", body: JSON.stringify(request), headers: { "Content-Type": "application/json" } }); }
}
