from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies.access import WorkspaceAccess, require_admin, require_permission
from app.models.access import AdminUser
from app.models.asset import (
    ArtifactInspection,
    AssetBundle,
    AssetStatusResponse,
    CreateAssetFromUrlRequest,
    IngestionDiagnostic,
    IndexDiagnostic,
    ProcessAssetRequest,
    ProcessingJob,
    UploadAssetRequest,
)
from app.services.asset_registry import (
    create_uploaded_asset,
    create_url_asset,
    get_artifact_inspection,
    get_asset_bundle,
    get_asset_status,
    list_assets,
    list_assets_for_admin,
    list_ingestion_diagnostics,
    list_index_diagnostics,
    list_processing_jobs,
    enqueue_index_reconciliation,
    retry_processing_job,
    process_asset,
)

router = APIRouter()


@router.get("/assets", response_model=list[AssetBundle], tags=["assets"])
def asset_list(
    access: Annotated[WorkspaceAccess, Depends(require_permission("assets.read"))],
) -> list[AssetBundle]:
    return list_assets(access.workspace)


@router.post("/assets/upload", response_model=AssetBundle, tags=["assets"])
def upload_asset(
    payload: UploadAssetRequest,
    access: Annotated[WorkspaceAccess, Depends(require_permission("assets.write"))],
) -> AssetBundle:
    return create_uploaded_asset(payload, access.workspace, actor=access.principal.actor)


@router.post("/assets/from-url", response_model=AssetBundle, tags=["assets"])
def asset_from_url(
    payload: CreateAssetFromUrlRequest,
    access: Annotated[WorkspaceAccess, Depends(require_permission("assets.write"))],
) -> AssetBundle:
    return create_url_asset(payload, access.workspace, actor=access.principal.actor)


@router.get("/assets/{asset_id}", response_model=AssetBundle, tags=["assets"])
def asset_detail(
    asset_id: str,
    access: Annotated[WorkspaceAccess, Depends(require_permission("assets.read"))],
) -> AssetBundle:
    bundle = get_asset_bundle(asset_id, access.workspace)
    if bundle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found.",
        )
    return bundle


@router.get("/assets/{asset_id}/status", response_model=AssetStatusResponse, tags=["assets"])
def asset_status(
    asset_id: str,
    access: Annotated[WorkspaceAccess, Depends(require_permission("assets.read"))],
) -> AssetStatusResponse:
    response = get_asset_status(asset_id, access.workspace)
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset status not found.",
        )
    return response


@router.post("/assets/{asset_id}/process", response_model=AssetStatusResponse, tags=["assets"])
def start_processing(
    asset_id: str,
    payload: ProcessAssetRequest,
    access: Annotated[WorkspaceAccess, Depends(require_permission("assets.write"))],
) -> AssetStatusResponse:
    response = process_asset(asset_id, payload, access.workspace)
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found.",
        )
    return response


@router.get("/admin/assets", response_model=list[AssetBundle], tags=["admin"])
def admin_asset_list(
    _: Annotated[AdminUser, Depends(require_admin("admin.support"))],
) -> list[AssetBundle]:
    return list_assets_for_admin()


@router.get(
    "/admin/ingestion/diagnostics",
    response_model=list[IngestionDiagnostic],
    tags=["admin"],
)
def ingestion_diagnostics(
    _: Annotated[AdminUser, Depends(require_admin("admin.support"))],
) -> list[IngestionDiagnostic]:
    return list_ingestion_diagnostics()


@router.get("/admin/jobs", response_model=list[ProcessingJob], tags=["admin"])
def admin_job_list(
    _: Annotated[AdminUser, Depends(require_admin("admin.support"))],
) -> list[ProcessingJob]:
    return list_processing_jobs()


@router.post("/admin/jobs/{job_id}/retry", response_model=ProcessingJob, tags=["admin"])
def retry_job(
    job_id: str,
    admin: Annotated[AdminUser, Depends(require_admin("admin.operate"))],
) -> ProcessingJob:
    job = retry_processing_job(job_id, actor=admin.email)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processing job not found.")
    return job


@router.get(
    "/admin/assets/{asset_id}/artifacts",
    response_model=ArtifactInspection,
    tags=["admin"],
)
def admin_artifact_inspection(
    asset_id: str,
    _: Annotated[AdminUser, Depends(require_admin("admin.support"))],
) -> ArtifactInspection:
    inspection = get_artifact_inspection(asset_id)
    if inspection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset artifacts not found.",
        )
    return inspection


@router.get(
    "/admin/index/diagnostics",
    response_model=list[IndexDiagnostic],
    tags=["admin"],
)
def index_diagnostics(
    _: Annotated[AdminUser, Depends(require_admin("admin.support"))],
) -> list[IndexDiagnostic]:
    return list_index_diagnostics()


@router.post(
    "/admin/index/reconcile",
    response_model=list[ProcessingJob],
    tags=["admin"],
)
def reconcile_indexes(
    _: Annotated[AdminUser, Depends(require_admin("admin.operate"))],
) -> list[ProcessingJob]:
    return enqueue_index_reconciliation()
