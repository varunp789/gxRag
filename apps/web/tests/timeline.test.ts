import { describe, expect, it } from "vitest";
import { buildTimeline, humanize, type AssetStatus, type JobStep } from "../lib/timeline";

const step = (order: number, name: string, over: Partial<JobStep> = {}): JobStep => ({
  id: `s${order}`, name, status: "pending", order, attempt_count: 0, max_retries: 2,
  started_at: null, completed_at: null, warnings: [], ...over,
});

const status = (steps: JobStep[], jobStatus = "completed", current = "completed", indexes: AssetStatus["indexes"] = []): AssetStatus => ({
  asset_id: "a1", asset_status: "ready", processing_status: jobStatus, indexes,
  current_job: { id: "j1", status: jobStatus, trigger: "manual", current_step: current, step_count: steps.length, completed_step_count: 0, steps },
});

describe("buildTimeline", () => {
  it("handles assets that were never processed", () => {
    const timeline = buildTimeline({ asset_id: "a", asset_status: "uploaded", processing_status: "idle", current_job: null, indexes: [] });
    expect(timeline).toEqual({ headline: "Not processed yet", progress: 0, entries: [], indexIssues: [] });
  });

  it("orders steps and reports progress", () => {
    const timeline = buildTimeline(status([step(2, "chunking", { status: "completed" }), step(1, "inspect_and_plan", { status: "completed" }), step(3, "embedding")], "running", "embedding"));
    expect(timeline.entries.map((e) => e.label)).toEqual(["Inspect and plan", "Chunking", "Embedding"]);
    expect(timeline.entries.map((e) => e.state)).toEqual(["done", "done", "active"]);
    expect(timeline.progress).toBe(67);
    expect(timeline.headline).toBe("Running — 2 of 3 steps complete");
  });

  it("surfaces failures, attempts, warnings and retryability", () => {
    const timeline = buildTimeline(status([step(1, "parse_ocr_stt", { status: "failed", attempt_count: 1, warnings: ["OCR provider unavailable"] })], "failed", "parse_ocr_stt"));
    expect(timeline.entries[0]).toMatchObject({ state: "failed", detail: "attempt 1/3 · OCR provider unavailable", retryable: true });
    const exhausted = buildTimeline(status([step(1, "parse_ocr_stt", { status: "failed", attempt_count: 3 })], "failed"));
    expect(exhausted.entries[0].retryable).toBe(false);
  });

  it("lists failed index writes", () => {
    const timeline = buildTimeline(status([step(1, "vector_index_write", { status: "completed" })], "completed_with_index_errors", "completed", [
      { index_type: "keyword", status: "failed", document_count: 0, metadata: { last_error: "opensearch unavailable" } },
      { index_type: "vector", status: "synced", document_count: 3, metadata: {} },
    ]));
    expect(timeline.indexIssues).toEqual(["Keyword index: opensearch unavailable"]);
  });

  it("does not divide by zero for empty jobs", () => {
    expect(buildTimeline(status([])).progress).toBe(0);
  });
});

describe("humanize", () => {
  it("formats step names", () => expect(humanize("graph_index_write")).toBe("Graph index write"));
});
