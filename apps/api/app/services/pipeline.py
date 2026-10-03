from dataclasses import dataclass
from datetime import datetime, timezone

from app.models.asset import Artifact, IndexRecord, IngestionAdapterDefinition, JobStep


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class AdapterResult:
    adapter_key: str
    normalized_output_format: str
    warnings: list[str]
    source_metadata: dict[str, str]
    artifact_type: str


@dataclass(frozen=True)
class PipelineStageResult:
    artifact_type: str
    output_format: str
    metadata: dict[str, str]
    warnings: list[str]


class IngestionAdapter:
    definition: IngestionAdapterDefinition

    def run(self, asset_id: str, workspace_id: str, title: str) -> AdapterResult:
        raise NotImplementedError


class PdfAdapter(IngestionAdapter):
    definition = IngestionAdapterDefinition(
        key="pdf",
        asset_types=["document"],
        supports_v1=True,
        normalized_output_format="markdown",
    )

    def run(self, asset_id: str, workspace_id: str, title: str) -> AdapterResult:
        return AdapterResult(
            adapter_key=self.definition.key,
            normalized_output_format=self.definition.normalized_output_format,
            warnings=[],
            source_metadata={"layout": "page-based", "ocr_fallback": "false"},
            artifact_type="normalized_raw_content",
        )


class ImageAdapter(IngestionAdapter):
    definition = IngestionAdapterDefinition(
        key="image",
        asset_types=["image"],
        supports_v1=False,
        normalized_output_format="ocr-json",
    )

    def run(self, asset_id: str, workspace_id: str, title: str) -> AdapterResult:
        return AdapterResult(
            adapter_key=self.definition.key,
            normalized_output_format=self.definition.normalized_output_format,
            warnings=["Image ingestion is scaffolded but not enabled in V1."],
            source_metadata={"layout": "region-based", "ocr_fallback": "true"},
            artifact_type="ocr_preview",
        )


class AudioAdapter(IngestionAdapter):
    definition = IngestionAdapterDefinition(
        key="audio",
        asset_types=["audio"],
        supports_v1=False,
        normalized_output_format="transcript-json",
    )

    def run(self, asset_id: str, workspace_id: str, title: str) -> AdapterResult:
        return AdapterResult(
            adapter_key=self.definition.key,
            normalized_output_format=self.definition.normalized_output_format,
            warnings=["Audio ingestion is scaffolded but not enabled in V1."],
            source_metadata={"transcript": "stub", "speaker_labels": "deferred"},
            artifact_type="transcript_preview",
        )


class SpreadsheetAdapter(IngestionAdapter):
    definition = IngestionAdapterDefinition(
        key="spreadsheet",
        asset_types=["spreadsheet"],
        supports_v1=True,
        normalized_output_format="table-json",
    )

    def run(self, asset_id: str, workspace_id: str, title: str) -> AdapterResult:
        return AdapterResult(
            adapter_key=self.definition.key,
            normalized_output_format=self.definition.normalized_output_format,
            warnings=[],
            source_metadata={"shape": "tabular", "header_inference": "enabled"},
            artifact_type="structured_table_preview",
        )


class WebContentAdapter(IngestionAdapter):
    definition = IngestionAdapterDefinition(
        key="web",
        asset_types=["web_page"],
        supports_v1=True,
        normalized_output_format="content-map-json",
    )

    def run(self, asset_id: str, workspace_id: str, title: str) -> AdapterResult:
        return AdapterResult(
            adapter_key=self.definition.key,
            normalized_output_format=self.definition.normalized_output_format,
            warnings=[],
            source_metadata={"fetch_mode": "url", "content_cleaning": "enabled"},
            artifact_type="web_content_preview",
        )


ADAPTERS: dict[str, IngestionAdapter] = {
    "document": PdfAdapter(),
    "image": ImageAdapter(),
    "audio": AudioAdapter(),
    "spreadsheet": SpreadsheetAdapter(),
    "web_page": WebContentAdapter(),
}

PROCESSING_STEP_NAMES = [
    "inspect_and_plan",
    "parse_ocr_stt",
    "normalize_and_structure",
    "chunking",
    "embedding",
    "entity_extraction",
    "relation_extraction",
    "graph_construction",
    "structured_data_registration",
]

INDEX_STEP_NAMES = [
    "vector_index_write",
    "keyword_index_write",
    "graph_index_write",
    "structured_index_write",
]

INDEX_BACKENDS = {
    "vector": "pgvector",
    "keyword": "opensearch",
    "graph": "arangodb",
    "structured": "postgres",
}


def get_adapter_for_asset_type(asset_type: str) -> IngestionAdapter:
    return ADAPTERS[asset_type]


def list_adapter_definitions() -> list[IngestionAdapterDefinition]:
    return [adapter.definition for adapter in ADAPTERS.values()]


def create_job_steps(job_id: str, adapter_key: str) -> list[JobStep]:
    step_names = PROCESSING_STEP_NAMES + INDEX_STEP_NAMES
    steps: list[JobStep] = []
    for index, step_name in enumerate(step_names):
        steps.append(
            JobStep(
                id=f"{job_id}_{step_name}",
                job_id=job_id,
                name=step_name,
                status="pending",
                order=index + 1,
                adapter_key=adapter_key,
                idempotency_key=f"{job_id}:{step_name}:v1",
                attempt_count=0,
                max_retries=2,
                resume_cursor=step_name,
            )
        )
    return steps


def run_processing_stages(
    *,
    asset_id: str,
    workspace_id: str,
    title: str,
    asset_type: str,
    adapter_result: AdapterResult,
    stats: dict[str, int] | None = None,
) -> list[PipelineStageResult]:
    stats = stats or {}

    def count(name: str, default: int) -> str:
        return str(stats.get(name, default))

    shared = {
        "asset_type": asset_type,
        "adapter_key": adapter_result.adapter_key,
        "title": title,
    }
    return [
        PipelineStageResult(
            artifact_type="processing_plan",
            output_format="json",
            metadata={**shared, "resume_strategy": "step-cursor", "mode": "inspection"},
            warnings=[],
        ),
        PipelineStageResult(
            artifact_type=adapter_result.artifact_type,
            output_format=adapter_result.normalized_output_format,
            metadata={**shared, **adapter_result.source_metadata},
            warnings=adapter_result.warnings,
        ),
        PipelineStageResult(
            artifact_type="structured_content",
            output_format="json",
            metadata={**shared, "schema": "v1-structured"},
            warnings=[],
        ),
        PipelineStageResult(
            artifact_type="content_chunks",
            output_format="jsonl",
            metadata={**shared, "chunk_strategy": "semantic-window", "chunk_count": count("chunk_count", 8)},
            warnings=[],
        ),
        PipelineStageResult(
            artifact_type="embedding_vectors",
            output_format="jsonl",
            metadata={**shared, "embedding_model": "local-trigram-256"},
            warnings=[],
        ),
        PipelineStageResult(
            artifact_type="entity_catalog",
            output_format="json",
            metadata={**shared, "entity_count": count("entity_count", 6)},
            warnings=[],
        ),
        PipelineStageResult(
            artifact_type="relation_catalog",
            output_format="json",
            metadata={**shared, "relation_count": count("relation_count", 7)},
            warnings=[],
        ),
        PipelineStageResult(
            artifact_type="graph_snapshot",
            output_format="json",
            metadata={**shared, "node_count": count("node_count", 6), "edge_count": count("edge_count", 7)},
            warnings=[],
        ),
        PipelineStageResult(
            artifact_type="structured_registry",
            output_format="json",
            metadata={**shared, "table_count": count("table_count", 1), "row_count": count("row_count", 24)},
            warnings=[],
        ),
    ]


def build_artifact(
    *,
    asset_id: str,
    workspace_id: str,
    adapter_key: str,
    artifact_type: str,
    output_format: str,
    warnings: list[str],
    producer_step: str,
    metadata: dict[str, str] | None = None,
    version: int = 1,
) -> Artifact:
    created_at = utc_now()
    return Artifact(
        id=f"artifact_{asset_id}_{producer_step}_{artifact_type}_v{version}",
        asset_id=asset_id,
        workspace_id=workspace_id,
        artifact_type=artifact_type,
        storage_path=(
            f"tenant/workspace/{workspace_id}/asset/{asset_id}/"
            f"{artifact_type}_v{version}.{output_format.replace('-', '.')}"
        ),
        format=output_format,
        version=version,
        producer_step=producer_step,
        metadata=metadata or {},
        provenance=[
            f"asset:{asset_id}",
            f"workspace:{workspace_id}",
            f"adapter:{adapter_key}",
            f"step:{producer_step}",
        ],
        warnings=warnings,
        created_at=created_at,
    )


def build_index_records(
    *,
    asset_id: str,
    workspace_id: str,
    artifact_ids: list[str],
    asset_type: str,
) -> list[IndexRecord]:
    updated_at = utc_now()
    return [
        IndexRecord(
            id=f"index_{asset_id}_vector",
            asset_id=asset_id,
            workspace_id=workspace_id,
            index_type="vector",
            storage_backend=INDEX_BACKENDS["vector"],
            status="synced",
            document_count=8,
            source_artifact_ids=artifact_ids,
            reconciliation_status="reconciled",
            metadata={"asset_type": asset_type, "writer": "vector_writer_v1"},
            updated_at=updated_at,
        ),
        IndexRecord(
            id=f"index_{asset_id}_keyword",
            asset_id=asset_id,
            workspace_id=workspace_id,
            index_type="keyword",
            storage_backend=INDEX_BACKENDS["keyword"],
            status="synced",
            document_count=8,
            source_artifact_ids=artifact_ids,
            reconciliation_status="reconciled",
            metadata={"asset_type": asset_type, "writer": "keyword_writer_v1"},
            updated_at=updated_at,
        ),
        IndexRecord(
            id=f"index_{asset_id}_graph",
            asset_id=asset_id,
            workspace_id=workspace_id,
            index_type="graph",
            storage_backend=INDEX_BACKENDS["graph"],
            status="synced",
            document_count=13,
            source_artifact_ids=artifact_ids,
            reconciliation_status="reconciled",
            metadata={"asset_type": asset_type, "writer": "graph_writer_v1"},
            updated_at=updated_at,
        ),
        IndexRecord(
            id=f"index_{asset_id}_structured",
            asset_id=asset_id,
            workspace_id=workspace_id,
            index_type="structured",
            storage_backend=INDEX_BACKENDS["structured"],
            status="synced" if asset_type == "spreadsheet" else "registered",
            document_count=24 if asset_type == "spreadsheet" else 1,
            source_artifact_ids=artifact_ids,
            reconciliation_status="reconciled",
            metadata={"asset_type": asset_type, "writer": "structured_writer_v1"},
            updated_at=updated_at,
        ),
    ]
