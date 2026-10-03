import { appConfig } from "./config";

/** Headers sent on every API call. A bearer token (user JWT or API key) wins over dev identity. */
export function buildHeaders(init?: HeadersInit, env: Record<string, string | undefined> = process.env): Record<string, string> {
  const headers: Record<string, string> = { Accept: "application/json" };
  const token = env.GXRAG_API_TOKEN;
  if (token) headers.Authorization = `Bearer ${token}`;
  else headers["X-Workspace-Id"] = env.GXRAG_WORKSPACE_ID ?? "ws_orbit_prod";
  if (token && env.GXRAG_WORKSPACE_ID) headers["X-Workspace-Id"] = env.GXRAG_WORKSPACE_ID;
  return { ...headers, ...(init ? Object.fromEntries(new Headers(init).entries()) : {}) };
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${appConfig.apiBaseUrl}/v1${path}`, {
    cache: "no-store",
    ...init,
    headers: buildHeaders(init?.headers),
  });
  if (!response.ok) throw new ApiError(response.status, `API request failed (${response.status})`);
  return response.json() as Promise<T>;
}
