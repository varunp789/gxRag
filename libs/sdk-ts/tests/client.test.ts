import { describe, expect, it, vi } from "vitest";
import { GXRagClient, GXRagError } from "../src/index";

const json = (status: number, body: unknown) => new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

describe("GXRagClient", () => {
  it("sends the key, workspace and JSON body", async () => {
    const fetchMock = vi.fn().mockResolvedValue(json(200, { results: [] }));
    const client = new GXRagClient("http://api/", { apiKey: "gxk_a_b", workspaceId: "ws_1", fetch: fetchMock });
    await client.hybrid({ query: "zarnotide", limit: 3 });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://api/v1/query/hybrid");
    expect(init.headers).toMatchObject({ Authorization: "Bearer gxk_a_b", "X-Workspace-Id": "ws_1", "Content-Type": "application/json" });
    expect(JSON.parse(init.body)).toEqual({ query: "zarnotide", limit: 3 });
  });

  it("omits auth headers when unset", async () => {
    const fetchMock = vi.fn().mockResolvedValue(json(200, { status: "ok" }));
    await new GXRagClient("http://api", { fetch: fetchMock }).health();
    expect(fetchMock.mock.calls[0][1].headers.Authorization).toBeUndefined();
  });

  it("raises typed errors with the server detail", async () => {
    const client = new GXRagClient("http://api", { fetch: vi.fn().mockResolvedValue(json(429, { detail: "query quota exceeded." })) });
    await expect(client.vector({ query: "x" })).rejects.toMatchObject({ name: "GXRagError", status: 429, detail: "query quota exceeded." });
    await expect(client.vector({ query: "x" })).rejects.toBeInstanceOf(GXRagError);
  });

  it("survives non-JSON error bodies", async () => {
    const client = new GXRagClient("http://api", { fetch: vi.fn().mockResolvedValue(new Response("boom", { status: 502, statusText: "Bad Gateway" })) });
    await expect(client.graph({ query: "x" })).rejects.toMatchObject({ status: 502, detail: "Bad Gateway" });
  });

  it("url-encodes asset ids", async () => {
    const fetchMock = vi.fn().mockResolvedValue(json(200, {}));
    await new GXRagClient("http://api", { fetch: fetchMock }).assetStatus("a/b");
    expect(fetchMock.mock.calls[0][0]).toBe("http://api/v1/assets/a%2Fb/status");
  });
});
