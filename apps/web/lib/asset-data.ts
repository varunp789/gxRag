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

