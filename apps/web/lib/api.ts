import { appConfig } from "./config";

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${appConfig.apiBaseUrl}/v1${path}`, { cache: "no-store", ...init, headers: { Accept: "application/json", "X-Workspace-Id": "ws_orbit_prod", ...init?.headers } });
  if (!response.ok) throw new Error(`API request failed (${response.status})`);
  return response.json() as Promise<T>;
}
