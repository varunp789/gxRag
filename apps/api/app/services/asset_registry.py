from datetime import datetime, timezone
from typing import Iterable
from uuid import uuid4

from app.models.asset import (
    Artifact,
    Asset,
    AssetBundle,
    AssetSource,
    AssetStatusResponse,
    AssetUpload,
    AssetVersion,
    CreateAssetFromUrlRequest,
    IngestionDiagnostic,
    ProcessingJob,
    JobStep,
    ProcessAssetRequest,
    UploadAssetRequest,
)
from app.models.access import Workspace
from app.services.catalog import get_workspace_scope
from app.services.pipeline import (
    build_artifact,
    get_adapter_for_asset_type,
    list_adapter_definitions,
    utc_now,
)


ASSETS: list[Asset] = []
ASSET_SOURCES: list[AssetSource] = []
ASSET_UPLOADS: list[AssetUpload] = []
ASSET_VERSIONS: list[AssetVersion] = []
ARTIFACTS: list[Artifact] = []
PROCESSING_JOBS: list[ProcessingJob] = []


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}"


def _find_asset(asset_id: str) -> Asset | None:
    return next((asset for asset in ASSETS if asset.id == asset_id), None)


def _find_job(job_id: str | None) -> ProcessingJob | None:
    if job_id is None:
        return None
    return next((job for job in PROCESSING_JOBS if job.id == job_id), None)


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


def _create_steps(job_id: str, adapter_key: str) -> list[JobStep]:
    step_names = [
        "receive_source",
        "normalize_source",
        "adapter_extract",
        "save_artifacts",
    ]
    steps: list[JobStep] = []
    for index, step_name in enumerate(step_names):
        status = "completed" if index < len(step_names) - 1 else "running"
        steps.append(
            JobStep(
                id=_new_id("step"),
                job_id=job_id,
                name=step_name,
                status=status,
                adapter_key=adapter_key,
            )
        )
    return steps


def _complete_steps(steps: list[JobStep], artifact_ids: Iterable[str], warnings: list[str]) -> list[JobStep]:
    updated: list[JobStep] = []
    for step in steps:
        status = "completed"
        step_warnings = warnings if step.name == "adapter_extract" else []
        step_artifacts = list(artifact_ids) if step.name == "save_artifacts" else []
        updated.append(
            step.model_copy(
                update={
                    "status": status,
                    "warnings": step_warnings,
                    "artifact_ids": step_artifacts,
                }
            )
        )
    return updated


def seed_assets() -> None:
    if ASSETS:
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
            name="receive_source",
            status="completed",
            adapter_key="pdf",
        ),
        JobStep(
            id="step_seed_2",
            job_id=job_id,
            name="normalize_source",
            status="completed",
            adapter_key="pdf",
        ),
        JobStep(
            id="step_seed_3",
            job_id=job_id,
            name="adapter_extract",
            status="completed",
            adapter_key="pdf",
        ),
        JobStep(
            id="step_seed_4",
            job_id=job_id,
            name="save_artifacts",
            status="completed",
            adapter_key="pdf",
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
            warnings=[],
            created_at=created_at,
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


def create_uploaded_asset(payload: UploadAssetRequest, workspace: Workspace) -> AssetBundle:
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
    return _bundle_for_asset(asset)


def create_url_asset(payload: CreateAssetFromUrlRequest, workspace: Workspace) -> AssetBundle:
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
    return _bundle_for_asset(asset)


def process_asset(asset_id: str, payload: ProcessAssetRequest, workspace: Workspace) -> AssetStatusResponse | None:
    seed_assets()
    asset = _find_asset(asset_id)
    if asset is None or not _asset_belongs_to_workspace(asset, workspace.id):
        return None

    adapter = get_adapter_for_asset_type(asset.asset_type)
    result = adapter.run(asset.id, workspace.id, asset.title)
    job_id = _new_id("job")
    job_steps = _create_steps(job_id, result.adapter_key)
    artifact = build_artifact(
        asset_id=asset.id,
        workspace_id=workspace.id,
        adapter_key=result.adapter_key,
        artifact_type=result.artifact_type,
        output_format=result.normalized_output_format,
        warnings=result.warnings,
    )
    ARTIFACTS.append(artifact)

    completed_steps = _complete_steps(job_steps, [artifact.id], result.warnings)
    processed_at = utc_now()
    job_status = "completed" if adapter.definition.supports_v1 else "needs_review"
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
        steps=completed_steps,
    )
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
    return get_asset_status(asset.id, workspace)


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

