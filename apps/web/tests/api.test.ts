import { describe, expect, it } from "vitest";
import { buildHeaders } from "../lib/api";

describe("buildHeaders", () => {
  it("falls back to the dev workspace header without a token", () => {
    expect(buildHeaders(undefined, {})).toEqual({ Accept: "application/json", "X-Workspace-Id": "ws_orbit_prod" });
  });

  it("prefers a bearer token and never sends a dev identity header", () => {
    const headers = buildHeaders(undefined, { GXRAG_API_TOKEN: "tok" });
    expect(headers.Authorization).toBe("Bearer tok");
    expect(headers["X-Actor-Email"]).toBeUndefined();
  });

  it("lets callers override headers", () => {
    expect(buildHeaders({ Accept: "text/plain" }, {}).accept).toBe("text/plain");
  });
});
