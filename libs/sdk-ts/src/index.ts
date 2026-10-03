export type QueryMode = "vector" | "hybrid" | "graph" | "multimodal" | "structured";
export type QueryRequest = { query: string; asset_id?: string; table_id?: string; limit?: number; filters?: Record<string, string> };
export type Citation = { asset_id: string; artifact_id: string; label: string; provenance: string[] };
export type QueryResponse = { mode: QueryMode; query: string; results: Array<{ id: string; kind: string; content: string; score: number; citation: Citation }>; citations: Citation[]; graph_paths: string[][]; table_refs: string[] };
export type AnswerResponse = { id: string; answer: string; model: string; cached: boolean; input_tokens: number; output_tokens: number; citations: Citation[] };

export class GXRagError extends Error {
  constructor(public readonly status: number, public readonly detail: string) {
    super(`gxRag request failed (${status}): ${detail}`);
    this.name = "GXRagError";
  }
}

export type ClientOptions = {
  /** Workspace API key (`gxk_...`) or user bearer token. */
  apiKey?: string;
  /** Only needed for user tokens that belong to several workspaces. */
  workspaceId?: string;
  fetch?: typeof fetch;
};

export class GXRagClient {
  private readonly fetchImpl: typeof fetch;
  constructor(private readonly baseUrl: string, private readonly options: ClientOptions = {}) {
    this.fetchImpl = options.fetch ?? ((input, init) => fetch(input, init));
  }

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    const headers: Record<string, string> = { Accept: "application/json" };
    if (this.options.apiKey) headers.Authorization = `Bearer ${this.options.apiKey}`;
    if (this.options.workspaceId) headers["X-Workspace-Id"] = this.options.workspaceId;
    const response = await this.fetchImpl(`${this.baseUrl.replace(/\/$/, "")}/v1${path}`, {
      ...init,
      headers: { ...headers, ...(init?.headers as Record<string, string> | undefined) },
    });
    if (!response.ok) {
      let detail = response.statusText;
      try {
        detail = ((await response.json()) as { detail?: string }).detail ?? detail;
      } catch {
        /* non-JSON error body */
      }
      throw new GXRagError(response.status, detail);
    }
    return response.json() as Promise<T>;
  }

  private post<T>(path: string, body: unknown) {
    return this.request<T>(path, { method: "POST", body: JSON.stringify(body), headers: { "Content-Type": "application/json" } });
  }

  health() { return this.request<{ status: string; service: string; timestamp: string }>("/health"); }
  query(mode: QueryMode, request: QueryRequest) { return this.post<QueryResponse>(`/query/${mode}`, request); }
  vector(request: QueryRequest) { return this.query("vector", request); }
  hybrid(request: QueryRequest) { return this.query("hybrid", request); }
  graph(request: QueryRequest) { return this.query("graph", request); }
  multimodal(request: QueryRequest) { return this.query("multimodal", request); }
  structured(request: QueryRequest) { return this.query("structured", request); }
  answer(mode: "hybrid" | "graph" | "multimodal", request: QueryRequest & { model?: string }) { return this.post<AnswerResponse>(`/answers/${mode}`, request); }
  assetStatus(assetId: string) { return this.request<{ asset_id: string; asset_status: string; processing_status: string }>(`/assets/${encodeURIComponent(assetId)}/status`); }
}
