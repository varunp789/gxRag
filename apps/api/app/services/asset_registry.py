import json
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from app.core.config import settings
from app.db import store as db_store
from app.models.access import Workspace
from app.models.asset import (
    Artifact,
    ArtifactInspection,
    Asset,
    AssetBundle,
    AssetSource,
    AssetStatusResponse,
    AssetUpload,
    AssetVersion,
    CreateAssetFromUrlRequest,
    IndexDiagnostic,
    IndexRecord,
    IngestionDiagnostic,
    JobStep,
    ProcessAssetRequest,
    ProcessingJob,
    UploadAssetRequest,
)
from app.services.catalog import get_workspace
from app.services.extractors import extract, read_source
from app.services.governance import audit, enforce_quota, record
from app.services.index_backends import write_graph, write_keyword, write_structured, write_vector
from app.services.job_queue import enqueue
from app.services.pipeline import (
    build_artifact,
    build_index_records,
    create_job_steps,
    get_adapter_for_asset_type,
    list_adapter_definitions,
    run_processing_stages,
    utc_now,
)
from app.services.text import chunk_text, extract_entities, extract_relations

ASSETS: list[Asset] = []
ASSET_SOURCES: list[AssetSource] = []
ASSET_UPLOADS: list[AssetUpload] = []
ASSET_VERSIONS: list[AssetVersion] = []
ARTIFACTS: list[Artifact] = []
PROCESSING_JOBS: list[ProcessingJob] = []
INDEX_RECORDS: list[IndexRecord] = []


def _state_path() -> Path:
    return Path(settings.processing_state_path)


def _snapshot() -> dict[str, list[dict]]:
    return {
        "assets": [item.model_dump(mode="json") for item in ASSETS],
        "sources": [item.model_dump(mode="json") for item in ASSET_SOURCES],
        "uploads": [item.model_dump(mode="json") for item in ASSET_UPLOADS],
        "versions": [item.model_dump(mode="json") for item in ASSET_VERSIONS],
        "artifacts": [item.model_dump(mode="json") for item in ARTIFACTS],
        "jobs": [item.model_dump(mode="json") for item in PROCESSING_JOBS],
        "indexes": [item.model_dump(mode="json") for item in INDEX_RECORDS],
    }


_json_mtime: list[float | None] = [None]


def _persist_state() -> None:
    if db_store.enabled():
        db_store.save_all(_snapshot())
        return
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(_snapshot(), indent=2))
    temp.replace(path)  # atomic: a concurrent reader never sees a half-written file
    _json_mtime[0] = path.stat().st_mtime_ns


def _apply_payload(payload: dict) -> None:
    """Replace in-memory state in place; other modules hold references to these lists."""
    ASSETS[:] = [Asset.model_validate(item) for item in payload["assets"]]
    ASSET_SOURCES[:] = [AssetSource.model_validate(item) for item in payload["sources"]]
    ASSET_UPLOADS[:] = [AssetUpload.model_validate(item) for item in payload["uploads"]]
    ASSET_VERSIONS[:] = [AssetVersion.model_validate(item) for item in payload["versions"]]
    ARTIFACTS[:] = [Artifact.model_validate(item) for item in payload["artifacts"]]
    PROCESSING_JOBS[:] = [ProcessingJob.model_validate(item) for item in payload["jobs"]]
    INDEX_RECORDS[:] = [IndexRecord.model_validate(item) for item in payload["indexes"]]


def _load_state() -> bool:
    if db_store.enabled():
        payload = db_store.load_all()
        if not payload["assets"]:
            return False
        _apply_payload(payload)
        return True
    path = _state_path()
    if not path.exists():
        return False
    _apply_payload(json.loads(path.read_text()))
    _json_mtime[0] = path.stat().st_mtime_ns
    return True


def reset_state() -> None:
    """Drop in-memory state (tests and fresh-process bootstrap)."""
    _apply_payload({key: [] for key in db_store.TABLES})
    _json_mtime[0] = None


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}"


def _find_asset(asset_id: str) -> Asset | None:
    return next((asset for asset in ASSETS if asset.id == asset_id), None)


def _find_job(job_id: str | None) -> ProcessingJob | None:
    if job_id is None:
        return None
    return next((job for job in PROCESSING_JOBS if job.id == job_id), None)


def _find_indexes(asset_id: str) -> list[IndexRecord]:
    return [record for record in INDEX_RECORDS if record.asset_id == asset_id]


def _asset_belongs_to_workspace(asset: Asset, workspace_id: str) -> bool:
    return asset.workspace_id == workspace_id


def _bundle_for_asset(asset: Asset) -> AssetBundle:
    source = next(source for source in ASSET_SOURCES if source.id == asset.source_id)
    version = next(version for version in ASSET_VERSIONS if version.id == asset.latest_version_id)
    upload = next((upload for upload in ASSET_UPLOADS if upload.asset_id == asset.id), None)
    jobs = [job for job in PROCESSING_JOBS if job.asset_id == asset.id]
    artifacts = [artifact for artifact in ARTIFACTS if artifact.asset_id == asset.id]
    return AssetBundle(
        asset=asset,
        source=source,
        version=version,
        upload=upload,
        jobs=jobs,
        artifacts=artifacts,
    )


def _complete_steps(
    steps: list[JobStep],
    artifact_ids: Iterable[str],
    warnings: list[str],
    started_at: str,
    completed_at: str,
) -> list[JobStep]:
    updated: list[JobStep] = []
    artifact_id_list = list(artifact_ids)
    for step in steps:
        step_warnings = warnings if step.name == "parse_ocr_stt" else []
        step_artifacts = artifact_id_list if step.name in {
            "structured_data_registration",
            "vector_index_write",
            "keyword_index_write",
            "graph_index_write",
            "structured_index_write",
        } else []
        updated.append(
            step.model_copy(
                update={
                    "status": "completed",
                    "attempt_count": 1,
                    "started_at": started_at,
                    "completed_at": completed_at,
                    "warnings": step_warnings,
                    "artifact_ids": step_artifacts,
                }
            )
        )
    return updated


def seed_assets() -> None:
    """Make in-memory state current; seed the demo asset into an empty store."""
    if db_store.enabled():
        # API and worker are separate processes: always read the shared database.
        if _load_state():
            return
        _apply_payload({key: [] for key in db_store.TABLES})
    elif ASSETS:
        # JSON dev store: pick up writes made by another process (API <-> worker).
        path = _state_path()
        if path.exists() and path.stat().st_mtime_ns != _json_mtime[0]:
            _load_state()
        return
    elif _load_state():
        return

    created_at = "2026-08-13T10:00:00Z"
    asset_id = "asset_orbit_trial_pdf"
    source_id = "source_orbit_trial_pdf"
    version_id = "version_orbit_trial_pdf"
    upload_id = "upload_orbit_trial_pdf"
    job_id = "job_orbit_trial_pdf"
    artifact_id = "artifact_orbit_trial_pdf_normalized"

    ASSET_SOURCES.append(
        AssetSource(
            id=source_id,
            asset_id=asset_id,
            source_type="upload",
            location="s3://workspace/ws_orbit_prod/quarterly-research.pdf",
            mime_type="application/pdf",
            created_at=created_at,
        )
    )
    ASSET_UPLOADS.append(
        AssetUpload(
            id=upload_id,
            asset_id=asset_id,
            file_name="quarterly-research.pdf",
            mime_type="application/pdf",
            size_bytes=1_280_550,
            uploaded_at=created_at,
        )
    )
    ASSET_VERSIONS.append(
        AssetVersion(
            id=version_id,
            asset_id=asset_id,
            version=1,
            created_at=created_at,
            status="active",
        )
    )
    job_steps = [
        JobStep(
            id="step_seed_1",
            job_id=job_id,
            name="inspect_and_plan",
            status="completed",
            order=1,
            adapter_key="pdf",
            idempotency_key="job_orbit_trial_pdf:inspect_and_plan:v1",
            attempt_count=1,
            max_retries=2,
            started_at=created_at,
            completed_at=created_at,
            resume_cursor="inspect_and_plan",
        ),
        JobStep(
            id="step_seed_2",
            job_id=job_id,
            name="parse_ocr_stt",
            status="completed",
            order=2,
            adapter_key="pdf",
            idempotency_key="job_orbit_trial_pdf:parse_ocr_stt:v1",
            attempt_count=1,
            max_retries=2,
            started_at=created_at,
            completed_at=created_at,
            resume_cursor="parse_ocr_stt",
        ),
        JobStep(
            id="step_seed_3",
            job_id=job_id,
            name="normalize_and_structure",
            status="completed",
            order=3,
            adapter_key="pdf",
            idempotency_key="job_orbit_trial_pdf:normalize_and_structure:v1",
            attempt_count=1,
            max_retries=2,
            started_at=created_at,
            completed_at=created_at,
            resume_cursor="normalize_and_structure",
        ),
        JobStep(
            id="step_seed_4",
            job_id=job_id,
            name="chunking",
            status="completed",
            order=4,
            adapter_key="pdf",
            idempotency_key="job_orbit_trial_pdf:chunking:v1",
            attempt_count=1,
            max_retries=2,
            started_at=created_at,
            completed_at=created_at,
            resume_cursor="chunking",
        ),
        JobStep(
            id="step_seed_5",
            job_id=job_id,
            name="embedding",
            status="completed",
            order=5,
            adapter_key="pdf",
            idempotency_key="job_orbit_trial_pdf:embedding:v1",
            attempt_count=1,
            max_retries=2,
            started_at=created_at,
            completed_at=created_at,
            resume_cursor="embedding",
        ),
        JobStep(
            id="step_seed_6",
            job_id=job_id,
            name="entity_extraction",
            status="completed",
            order=6,
            adapter_key="pdf",
            idempotency_key="job_orbit_trial_pdf:entity_extraction:v1",
            attempt_count=1,
            max_retries=2,
            started_at=created_at,
            completed_at=created_at,
            resume_cursor="entity_extraction",
        ),
        JobStep(
            id="step_seed_7",
            job_id=job_id,
            name="relation_extraction",
            status="completed",
            order=7,
            adapter_key="pdf",
            idempotency_key="job_orbit_trial_pdf:relation_extraction:v1",
            attempt_count=1,
            max_retries=2,
            started_at=created_at,
            completed_at=created_at,
            resume_cursor="relation_extraction",
        ),
        JobStep(
            id="step_seed_8",
            job_id=job_id,
            name="graph_construction",
            status="completed",
            order=8,
            adapter_key="pdf",
            idempotency_key="job_orbit_trial_pdf:graph_construction:v1",
            attempt_count=1,
            max_retries=2,
            started_at=created_at,
            completed_at=created_at,
            resume_cursor="graph_construction",
        ),
        JobStep(
            id="step_seed_9",
            job_id=job_id,
            name="structured_data_registration",
            status="completed",
            order=9,
            adapter_key="pdf",
            idempotency_key="job_orbit_trial_pdf:structured_data_registration:v1",
            attempt_count=1,
            max_retries=2,
            started_at=created_at,
            completed_at=created_at,
            resume_cursor="structured_data_registration",
            artifact_ids=[artifact_id],
        ),
        JobStep(
            id="step_seed_10",
            job_id=job_id,
            name="vector_index_write",
            status="completed",
            order=10,
            adapter_key="pdf",
            idempotency_key="job_orbit_trial_pdf:vector_index_write:v1",
            attempt_count=1,
            max_retries=2,
            started_at=created_at,
            completed_at=created_at,
            resume_cursor="vector_index_write",
            artifact_ids=[artifact_id],
        ),
        JobStep(
            id="step_seed_11",
            job_id=job_id,
            name="keyword_index_write",
            status="completed",
            order=11,
            adapter_key="pdf",
            idempotency_key="job_orbit_trial_pdf:keyword_index_write:v1",
            attempt_count=1,
            max_retries=2,
            started_at=created_at,
            completed_at=created_at,
            resume_cursor="keyword_index_write",
            artifact_ids=[artifact_id],
        ),
        JobStep(
            id="step_seed_12",
            job_id=job_id,
            name="graph_index_write",
            status="completed",
            order=12,
            adapter_key="pdf",
            idempotency_key="job_orbit_trial_pdf:graph_index_write:v1",
            attempt_count=1,
            max_retries=2,
            started_at=created_at,
            completed_at=created_at,
            resume_cursor="graph_index_write",
            artifact_ids=[artifact_id],
        ),
        JobStep(
            id="step_seed_13",
            job_id=job_id,
            name="structured_index_write",
            status="completed",
            order=13,
            adapter_key="pdf",
            idempotency_key="job_orbit_trial_pdf:structured_index_write:v1",
            attempt_count=1,
            max_retries=2,
            started_at=created_at,
            completed_at=created_at,
            resume_cursor="structured_index_write",
            artifact_ids=[artifact_id],
        ),
    ]
    PROCESSING_JOBS.append(
        ProcessingJob(
            id=job_id,
            asset_id=asset_id,
            workspace_id="ws_orbit_prod",
            status="completed",
            trigger="manual",
            created_at=created_at,
            updated_at=created_at,
            current_step="completed",
            step_count=len(job_steps),
            retryable_steps=[step.name for step in job_steps],
            completed_step_count=len(job_steps),
            steps=job_steps,
        )
    )
    ARTIFACTS.append(
        Artifact(
            id=artifact_id,
            asset_id=asset_id,
            workspace_id="ws_orbit_prod",
            artifact_type="normalized_raw_content",
            storage_path=(
                "tenant/workspace/ws_orbit_prod/asset/asset_orbit_trial_pdf/"
                "normalized_raw_content.markdown"
            ),
            format="markdown",
            version=1,
            producer_step="parse_ocr_stt",
            metadata={"layout": "page-based"},
            provenance=[
                "asset:asset_orbit_trial_pdf",
                "workspace:ws_orbit_prod",
                "adapter:pdf",
                "step:parse_ocr_stt",
            ],
            warnings=[],
            created_at=created_at,
        )
    )
    INDEX_RECORDS.extend(
        build_index_records(
            asset_id=asset_id,
            workspace_id="ws_orbit_prod",
            artifact_ids=[artifact_id],
            asset_type="document",
        )
    )
    ASSETS.append(
        Asset(
            id=asset_id,
            workspace_id="ws_orbit_prod",
            tenant_id="tenant_orbit",
            asset_type="document",
            title="Quarterly Research Report",
            source_type="upload",
            status="ready",
            ingestion_status="normalized",
            processing_status="completed",
            created_at=created_at,
            updated_at=created_at,
            latest_version_id=version_id,
            source_id=source_id,
            upload_id=upload_id,
            current_job_id=job_id,
            adapter_key="pdf",
            warnings=[],
            tags=["research", "quarterly"],
        )
    )
    _persist_state()


def list_assets(workspace: Workspace) -> list[AssetBundle]:
    seed_assets()
    return [
        _bundle_for_asset(asset)
        for asset in ASSETS
        if _asset_belongs_to_workspace(asset, workspace.id)
    ]


def get_asset_bundle(asset_id: str, workspace: Workspace) -> AssetBundle | None:
    seed_assets()
    asset = _find_asset(asset_id)
    if asset is None or not _asset_belongs_to_workspace(asset, workspace.id):
        return None
    return _bundle_for_asset(asset)


def create_uploaded_asset(payload: UploadAssetRequest, workspace: Workspace, actor: str = "system") -> AssetBundle:
    enforce_quota(workspace.id, "document")
    created_at = utc_now()
    asset_id = _new_id("asset")
    source_id = _new_id("source")
    upload_id = _new_id("upload")
    version_id = _new_id("version")

    source = AssetSource(
        id=source_id,
        asset_id=asset_id,
        source_type="upload",
        location=f"staged://{workspace.id}/{payload.file_name}",
        mime_type=payload.mime_type,
        created_at=created_at,
        content_base64=payload.content_base64,
    )
    upload = AssetUpload(
        id=upload_id,
        asset_id=asset_id,
        file_name=payload.file_name,
        mime_type=payload.mime_type,
        size_bytes=payload.size_bytes,
        uploaded_at=created_at,
    )
    version = AssetVersion(
        id=version_id,
        asset_id=asset_id,
        version=1,
        created_at=created_at,
        status="draft",
    )
    adapter = get_adapter_for_asset_type(payload.asset_type)
    asset = Asset(
        id=asset_id,
        workspace_id=workspace.id,
        tenant_id=workspace.tenant_id,
        asset_type=payload.asset_type,
        title=payload.title,
        source_type="upload",
        status="uploaded",
        ingestion_status="received",
        processing_status="idle",
        created_at=created_at,
        updated_at=created_at,
        latest_version_id=version_id,
        source_id=source_id,
        upload_id=upload_id,
        current_job_id=None,
        adapter_key=adapter.definition.key,
        warnings=[],
        tags=payload.tags,
    )

    ASSET_SOURCES.append(source)
    ASSET_UPLOADS.append(upload)
    ASSET_VERSIONS.append(version)
    ASSETS.append(asset)
    _persist_state()
    record(workspace.id, "document")
    audit(actor, "asset.uploaded", "asset", asset.id, workspace.id)
    return _bundle_for_asset(asset)


def create_url_asset(payload: CreateAssetFromUrlRequest, workspace: Workspace, actor: str = "system") -> AssetBundle:
    enforce_quota(workspace.id, "document")
    created_at = utc_now()
    asset_id = _new_id("asset")
    source_id = _new_id("source")
    version_id = _new_id("version")

    source = AssetSource(
        id=source_id,
        asset_id=asset_id,
        source_type="url",
        location=str(payload.url),
        mime_type=payload.mime_type,
        created_at=created_at,
    )
    version = AssetVersion(
        id=version_id,
        asset_id=asset_id,
        version=1,
        created_at=created_at,
        status="draft",
    )
    adapter = get_adapter_for_asset_type(payload.asset_type)
    asset = Asset(
        id=asset_id,
        workspace_id=workspace.id,
        tenant_id=workspace.tenant_id,
        asset_type=payload.asset_type,
        title=payload.title,
        source_type="url",
        status="registered",
        ingestion_status="received",
        processing_status="idle",
        created_at=created_at,
        updated_at=created_at,
        latest_version_id=version_id,
        source_id=source_id,
        upload_id=None,
        current_job_id=None,
        adapter_key=adapter.definition.key,
        warnings=[],
        tags=payload.tags,
    )
    ASSET_SOURCES.append(source)
    ASSET_VERSIONS.append(version)
    ASSETS.append(asset)
    _persist_state()
    record(workspace.id, "document")
    audit(actor, "asset.registered", "asset", asset.id, workspace.id)
    return _bundle_for_asset(asset)


def _execute_asset(
    asset_id: str,
    payload: ProcessAssetRequest,
    workspace: Workspace,
    job_id: str | None = None,
) -> AssetStatusResponse | None:
    seed_assets()
    asset = _find_asset(asset_id)
    if asset is None or not _asset_belongs_to_workspace(asset, workspace.id):
        return None

    adapter = get_adapter_for_asset_type(asset.asset_type)
    source = next(source for source in ASSET_SOURCES if source.id == asset.source_id)
    extracted = extract(
        asset.asset_type,
        read_source(source.location, source.content_base64),
        source.location.rsplit("/", 1)[-1],
    )
    adapter_result = adapter.run(asset.id, workspace.id, asset.title)
    result = adapter_result.model_copy() if hasattr(adapter_result, "model_copy") else adapter_result
    # Adapter metadata remains useful, while provider output is the source of truth.
    result = type(adapter_result)(
        adapter_key=adapter_result.adapter_key,
        normalized_output_format=adapter_result.normalized_output_format,
        warnings=[*adapter_result.warnings, *extracted.warnings],
        source_metadata={**adapter_result.source_metadata, "provider": extracted.provider,
                         "evidence_count": str(len(extracted.evidence)), "character_count": str(len(extracted.text))},
        artifact_type=adapter_result.artifact_type,
    )
    job_id = job_id or _new_id("job")
    job_steps = create_job_steps(job_id, result.adapter_key)
    artifact_version = 1 + max((artifact.version for artifact in ARTIFACTS if artifact.asset_id == asset.id), default=0)
    chunks = chunk_text(extracted.text) or [asset.title]
    entities = extract_entities(extracted.text)
    relations = extract_relations(chunks, entities)
    stages = run_processing_stages(
        asset_id=asset.id,
        workspace_id=workspace.id,
        title=asset.title,
        asset_type=asset.asset_type,
        adapter_result=result,
        stats={
            "chunk_count": len(chunks), "entity_count": len(entities), "relation_count": len(relations),
            "node_count": len(entities), "edge_count": len(relations),
            "table_count": 1 if extracted.rows else 0, "row_count": len(extracted.rows),
        },
    )
    produced_artifacts: list[Artifact] = []
    step_names = [step.name for step in job_steps]
    for step_name, stage in zip(step_names, stages):
        produced_artifacts.append(
            build_artifact(
                asset_id=asset.id,
                workspace_id=workspace.id,
                adapter_key=result.adapter_key,
                artifact_type=stage.artifact_type,
                output_format=stage.output_format,
                warnings=stage.warnings,
                producer_step=step_name,
                metadata=stage.metadata,
                version=artifact_version,
            )
        )
    ARTIFACTS.extend(produced_artifacts)

    artifact_root = Path(settings.artifact_root) / workspace.id / asset.id / f"v{artifact_version}"
    artifact_root.mkdir(parents=True, exist_ok=True)
    (artifact_root / "raw_extracted.md").write_text(extracted.text)
    (artifact_root / "provenance.json").write_text(json.dumps(extracted.evidence, indent=2))
    if extracted.rows:
        (artifact_root / "structured_rows.json").write_text(json.dumps(extracted.rows, indent=2))

    index_records = build_index_records(
        asset_id=asset.id,
        workspace_id=workspace.id,
        artifact_ids=[artifact.id for artifact in produced_artifacts],
        asset_type=asset.asset_type,
    )
    writers = {
        "vector": lambda: write_vector(workspace_id=workspace.id, asset_id=asset.id, chunks=chunks),
        "keyword": lambda: write_keyword(workspace_id=workspace.id, asset_id=asset.id, title=asset.title, chunks=chunks),
        "graph": lambda: write_graph(workspace_id=workspace.id, asset_id=asset.id, entities=entities, relations=relations),
        "structured": lambda: write_structured(workspace_id=workspace.id, asset_id=asset.id, rows=extracted.rows),
    }
    observed_indexes: list[IndexRecord] = []
    for index_record in index_records:
        try:
            written = writers[index_record.index_type]()
            observed_indexes.append(index_record.model_copy(update={
                "status": "synced", "document_count": written.document_count,
                "reconciliation_status": "reconciled",
                "metadata": {**index_record.metadata, "external_id": written.external_id},
            }))
        except Exception as error:
            observed_indexes.append(index_record.model_copy(update={
                "status": "failed", "document_count": 0, "reconciliation_status": "pending",
                "metadata": {**index_record.metadata, "last_error": str(error)},
            }))
    INDEX_RECORDS[:] = [record for record in INDEX_RECORDS if record.asset_id != asset.id]
    INDEX_RECORDS.extend(observed_indexes)

    processed_at = utc_now()
    completed_steps = _complete_steps(
        job_steps,
        [artifact.id for artifact in produced_artifacts],
        result.warnings,
        processed_at,
        processed_at,
    )
    failed_index_types = {record.index_type for record in observed_indexes if record.status == "failed"}
    completed_steps = [
        step.model_copy(update={
            "status": "failed",
            "warnings": [next(record.metadata.get("last_error", "Index write failed.") for record in observed_indexes if record.index_type == step.name.removesuffix("_index_write"))],
        }) if step.name.removesuffix("_index_write") in failed_index_types else step
        for step in completed_steps
    ]
    job_status = (
        "needs_review" if not adapter.definition.supports_v1
        else "completed_with_index_errors" if failed_index_types
        else "completed"
    )
    job = ProcessingJob(
        id=job_id,
        asset_id=asset.id,
        workspace_id=workspace.id,
        status=job_status,
        trigger=payload.trigger,
        created_at=processed_at,
        updated_at=processed_at,
        current_step="completed",
        step_count=len(completed_steps),
        retryable_steps=[step.name for step in completed_steps],
        completed_step_count=len([step for step in completed_steps if step.status == "completed"]),
        steps=completed_steps,
    )
    PROCESSING_JOBS[:] = [existing for existing in PROCESSING_JOBS if existing.id != job.id]
    PROCESSING_JOBS.append(job)

    version = next(version for version in ASSET_VERSIONS if version.id == asset.latest_version_id)
    version_index = ASSET_VERSIONS.index(version)
    ASSET_VERSIONS[version_index] = version.model_copy(update={"status": "active"})

    asset_index = ASSETS.index(asset)
    ASSETS[asset_index] = asset.model_copy(
        update={
            "status": "ready" if adapter.definition.supports_v1 else "review_required",
            "ingestion_status": "normalized",
            "processing_status": job_status,
            "updated_at": processed_at,
            "current_job_id": job.id,
            "warnings": result.warnings,
            "adapter_key": result.adapter_key,
        }
    )
    _persist_state()
    return get_asset_status(asset.id, workspace)


def process_asset(asset_id: str, payload: ProcessAssetRequest, workspace: Workspace) -> AssetStatusResponse | None:
    """Create durable work first; a worker performs all processing stages."""
    seed_assets()
    asset = _find_asset(asset_id)
    if asset is None or not _asset_belongs_to_workspace(asset, workspace.id):
        return None
    adapter = get_adapter_for_asset_type(asset.asset_type)
    if payload.content_base64:
        source = next(source for source in ASSET_SOURCES if source.id == asset.source_id)
        ASSET_SOURCES[ASSET_SOURCES.index(source)] = source.model_copy(
            update={"content_base64": payload.content_base64}
        )
    queued_at = utc_now()
    job_id = _new_id("job")
    steps = create_job_steps(job_id, adapter.definition.key)
    job = ProcessingJob(
        id=job_id, asset_id=asset.id, workspace_id=workspace.id, status="queued",
        trigger=payload.trigger, created_at=queued_at, updated_at=queued_at,
        current_step="inspect_and_plan", step_count=len(steps),
        retryable_steps=[step.name for step in steps], steps=steps,
    )
    PROCESSING_JOBS.append(job)
    ASSETS[ASSETS.index(asset)] = asset.model_copy(update={
        "status": "processing", "processing_status": "queued", "current_job_id": job_id,
        "updated_at": queued_at,
    })
    _persist_state()
    enqueue(job_id)
    return get_asset_status(asset.id, workspace)


def run_queued_job(job_id: str) -> ProcessingJob | None:
    """Worker entry point. Exceptions are recorded for operator retry/reprocess."""
    seed_assets()
    job = _find_job(job_id)
    if job is None or job.status not in {"queued", "retrying"}:
        return job
    workspace = get_workspace(job.workspace_id)
    if workspace is None:
        return None
    try:
        _execute_asset(job.asset_id, ProcessAssetRequest(trigger=job.trigger), workspace, job_id=job.id)
    except Exception as error:
        now = utc_now()
        failed_steps = [
            step.model_copy(update={"status": "failed", "attempt_count": step.attempt_count + 1,
                                    "completed_at": now, "warnings": [str(error)]})
            if step.name == job.current_step else step
            for step in job.steps
        ]
        failed = job.model_copy(update={"status": "failed", "updated_at": now, "steps": failed_steps})
        PROCESSING_JOBS[PROCESSING_JOBS.index(job)] = failed
        asset = _find_asset(job.asset_id)
        if asset is not None:
            ASSETS[ASSETS.index(asset)] = asset.model_copy(update={
                "status": "failed", "processing_status": "failed", "updated_at": now,
                "warnings": [str(error)],
            })
        _persist_state()
        return failed
    return _find_job(job_id)


def retry_processing_job(job_id: str, actor: str = "platform_admin") -> ProcessingJob | None:
    seed_assets()
    job = _find_job(job_id)
    if job is None:
        return None
    now = utc_now()
    retried_steps = [
        step.model_copy(update={"status": "pending", "completed_at": None, "warnings": []})
        if step.status == "failed" else step
        for step in job.steps
    ]
    retried = job.model_copy(update={
        "status": "retrying", "updated_at": now, "current_step": "inspect_and_plan",
        "steps": retried_steps,
    })
    PROCESSING_JOBS[PROCESSING_JOBS.index(job)] = retried
    _persist_state()
    audit(actor, "processing_job.retry_requested", "processing_job", job_id, job.workspace_id)
    enqueue(job_id)
    return retried


def get_asset_status(asset_id: str, workspace: Workspace) -> AssetStatusResponse | None:
    bundle = get_asset_bundle(asset_id, workspace)
    if bundle is None:
        return None
    current_job = _find_job(bundle.asset.current_job_id)
    return AssetStatusResponse(
        asset_id=bundle.asset.id,
        workspace_id=bundle.asset.workspace_id,
        asset_status=bundle.asset.status,
        ingestion_status=bundle.asset.ingestion_status,
        processing_status=bundle.asset.processing_status,
        current_job=current_job,
        artifacts=bundle.artifacts,
        indexes=_find_indexes(bundle.asset.id),
    )


def list_ingestion_diagnostics() -> list[IngestionDiagnostic]:
    seed_assets()
    diagnostics: list[IngestionDiagnostic] = []
    definitions = list_adapter_definitions()
    for definition in definitions:
        asset_count = len(
            [asset for asset in ASSETS if asset.adapter_key == definition.key]
        )
        job_count = len(
            [
                job
                for job in PROCESSING_JOBS
                if any(step.adapter_key == definition.key for step in job.steps)
            ]
        )
        warnings = [
            warning
            for artifact in ARTIFACTS
            for warning in artifact.warnings
            if artifact.asset_id in [asset.id for asset in ASSETS if asset.adapter_key == definition.key]
        ]
        latest_asset = next(
            (asset for asset in reversed(ASSETS) if asset.adapter_key == definition.key),
            None,
        )
        diagnostics.append(
            IngestionDiagnostic(
                adapter=definition,
                asset_count=asset_count,
                job_count=job_count,
                recent_warning_count=len(warnings),
                latest_asset_id=latest_asset.id if latest_asset else None,
            )
        )
    return diagnostics


def list_assets_for_admin() -> list[AssetBundle]:
    seed_assets()
    return [_bundle_for_asset(asset) for asset in ASSETS]


def list_processing_jobs() -> list[ProcessingJob]:
    seed_assets()
    return list(reversed(PROCESSING_JOBS))


def get_artifact_inspection(asset_id: str) -> ArtifactInspection | None:
    seed_assets()
    asset = _find_asset(asset_id)
    if asset is None:
        return None
    return ArtifactInspection(
        asset_id=asset.id,
        workspace_id=asset.workspace_id,
        artifacts=[artifact for artifact in ARTIFACTS if artifact.asset_id == asset.id],
        indexes=_find_indexes(asset.id),
    )


def list_index_diagnostics() -> list[IndexDiagnostic]:
    seed_assets()
    diagnostics: list[IndexDiagnostic] = []
    for index_type in ["vector", "keyword", "graph", "structured"]:
        records = [record for record in INDEX_RECORDS if record.index_type == index_type]
        latest = max(records, key=lambda record: record.updated_at) if records else None
        diagnostics.append(
            IndexDiagnostic(
                index_type=index_type,
                storage_backend=records[0].storage_backend if records else "unconfigured",
                record_count=len(records),
                synced_count=len([record for record in records if record.status == "synced"]),
                stale_count=len(
                    [record for record in records if record.reconciliation_status != "reconciled"]
                ),
                latest_asset_id=latest.asset_id if latest else None,
                last_updated_at=latest.updated_at if latest else None,
            )
        )
    return diagnostics


def enqueue_index_reconciliation() -> list[ProcessingJob]:
    """Persist retries for stale/failed index records through the normal worker queue."""
    seed_assets()
    queued: list[ProcessingJob] = []
    affected_asset_ids = {
        record.asset_id for record in INDEX_RECORDS
        if record.status == "failed" or record.reconciliation_status != "reconciled"
    }
    for asset_id in affected_asset_ids:
        asset = _find_asset(asset_id)
        if asset is None:
            continue
        workspace = get_workspace(asset.workspace_id)
        if workspace is None:
            continue
        response = process_asset(asset_id, ProcessAssetRequest(trigger="index_reconciliation"), workspace)
        if response and response.current_job:
            queued.append(response.current_job)
    return queued
