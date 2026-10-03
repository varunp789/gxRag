export type JobStep = {
  id: string;
  name: string;
  status: string;
  order: number;
  attempt_count: number;
  max_retries: number;
  started_at: string | null;
  completed_at: string | null;
  warnings: string[];
};

export type ProcessingJob = {
  id: string;
  status: string;
  trigger: string;
  current_step: string;
  step_count: number;
  completed_step_count: number;
  steps: JobStep[];
};

export type AssetStatus = {
  asset_id: string;
  asset_status: string;
  processing_status: string;
  current_job: ProcessingJob | null;
  indexes: { index_type: string; status: string; document_count: number; metadata: Record<string, string> }[];
};

export type TimelineEntry = {
  id: string;
  label: string;
  state: "done" | "active" | "failed" | "pending";
  detail: string;
  retryable: boolean;
};

export type Timeline = {
  headline: string;
  progress: number;
  entries: TimelineEntry[];
  indexIssues: string[];
};

export function humanize(stepName: string): string {
  const text = stepName.replace(/_/g, " ").trim();
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function stateOf(step: JobStep, job: ProcessingJob): TimelineEntry["state"] {
  if (step.status === "completed") return "done";
  if (step.status === "failed") return "failed";
  if (job.status === "queued" || job.status === "retrying" || job.status === "running") {
    if (step.name === job.current_step) return "active";
  }
  return "pending";
}

export function buildTimeline(status: AssetStatus): Timeline {
  const job = status.current_job;
  if (!job) {
    return { headline: "Not processed yet", progress: 0, entries: [], indexIssues: [] };
  }
  const steps = [...job.steps].sort((a, b) => a.order - b.order);
  const entries = steps.map((step): TimelineEntry => {
    const state = stateOf(step, job);
    const parts: string[] = [];
    if (step.attempt_count > 0) parts.push(`attempt ${step.attempt_count}/${step.max_retries + 1}`);
    if (step.warnings.length > 0) parts.push(step.warnings[0]);
    return { id: step.id, label: humanize(step.name), state, detail: parts.join(" · "), retryable: state === "failed" && step.attempt_count <= step.max_retries };
  });
  const done = entries.filter((entry) => entry.state === "done").length;
  const indexIssues = status.indexes
    .filter((index) => index.status === "failed")
    .map((index) => `${humanize(index.index_type)} index: ${index.metadata.last_error ?? "write failed"}`);
  return {
    headline: `${humanize(job.status)} — ${done} of ${steps.length} steps complete`,
    progress: steps.length === 0 ? 0 : Math.round((done / steps.length) * 100),
    entries,
    indexIssues,
  };
}
