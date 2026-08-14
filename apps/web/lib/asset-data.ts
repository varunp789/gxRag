export const assetSummary = [
  {
    id: "asset_orbit_trial_pdf",
    title: "Quarterly Research Report",
    assetType: "document",
    sourceType: "upload",
    status: "ready",
    processingStatus: "completed",
    workspace: "Orbit Production",
    adapter: "pdf",
    currentStep: "completed",
    artifacts: 9,
    indexes: 4,
  },
  {
    id: "asset_orbit_site",
    title: "Orbit Product Launch Notes",
    assetType: "web_page",
    sourceType: "url",
    status: "registered",
    processingStatus: "idle",
    workspace: "Orbit Research",
    adapter: "web",
    currentStep: "inspect_and_plan",
    artifacts: 0,
    indexes: 0,
  },
];

export const uploadModes = [
  {
    label: "File upload",
    description: "PDF, CSV, Excel, and future multimodal uploads.",
  },
  {
    label: "URL ingestion",
    description: "Register web content for normalization and chunking.",
  },
];

export const adapterDiagnostics = [
  {
    adapter: "pdf",
    supported: "V1",
    output: "markdown",
    notes: "Primary path for document ingestion.",
  },
  {
    adapter: "spreadsheet",
    supported: "V1",
    output: "table-json",
    notes: "Structured table extraction path.",
  },
  {
    adapter: "web",
    supported: "V1",
    output: "content-map-json",
    notes: "Fetch and clean web content before chunking.",
  },
  {
    adapter: "image",
    supported: "Deferred",
    output: "ocr-json",
    notes: "Scaffolded only for later OCR expansion.",
  },
  {
    adapter: "audio",
    supported: "Deferred",
    output: "transcript-json",
    notes: "Scaffolded only for later STT expansion.",
  },
];

export const processingQueue = [
  {
    jobId: "job_orbit_trial_pdf",
    assetTitle: "Quarterly Research Report",
    status: "completed",
    currentStep: "structured_index_write",
    completedSteps: "13/13",
    resumable: "yes",
  },
  {
    jobId: "job_orbit_site",
    assetTitle: "Orbit Product Launch Notes",
    status: "queued",
    currentStep: "inspect_and_plan",
    completedSteps: "0/13",
    resumable: "yes",
  },
];

export const artifactInspection = [
  {
    artifact: "processing_plan",
    format: "json",
    producer: "inspect_and_plan",
    version: "v1",
  },
  {
    artifact: "content_chunks",
    format: "jsonl",
    producer: "chunking",
    version: "v1",
  },
  {
    artifact: "graph_snapshot",
    format: "json",
    producer: "graph_construction",
    version: "v1",
  },
  {
    artifact: "structured_registry",
    format: "json",
    producer: "structured_data_registration",
    version: "v1",
  },
];

export const indexDiagnostics = [
  {
    index: "vector",
    backend: "pgvector",
    status: "synced",
    reconciliation: "reconciled",
  },
  {
    index: "keyword",
    backend: "opensearch",
    status: "synced",
    reconciliation: "reconciled",
  },
  {
    index: "graph",
    backend: "arangodb",
    status: "synced",
    reconciliation: "reconciled",
  },
  {
    index: "structured",
    backend: "postgres",
    status: "registered",
    reconciliation: "reconciled",
  },
];
