from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies.access import get_current_admin, get_current_workspace
from app.models.access import AdminUser, Workspace
from app.models.asset import (
    AssetBundle,
    AssetStatusResponse,
    CreateAssetFromUrlRequest,
    IngestionDiagnostic,
    ProcessAssetRequest,
    UploadAssetRequest,
)
from app.services.asset_registry import (
    create_uploaded_asset,
    create_url_asset,
    get_asset_bundle,
    get_asset_status,
    list_assets,
    list_assets_for_admin,
    list_ingestion_diagnostics,
    process_asset,
)

router = APIRouter()


@router.get("/assets", response_model=list[AssetBundle], tags=["assets"])
def asset_list(
    workspace: Annotated[Workspace, Depends(get_current_workspace)],
) -> list[AssetBundle]:
    return list_assets(workspace)


@router.post("/assets/upload", response_model=AssetBundle, tags=["assets"])
def upload_asset(
    payload: UploadAssetRequest,
    workspace: Annotated[Workspace, Depends(get_current_workspace)],
) -> AssetBundle:
    return create_uploaded_asset(payload, workspace)


@router.post("/assets/from-url", response_model=AssetBundle, tags=["assets"])
def asset_from_url(
    payload: CreateAssetFromUrlRequest,
    workspace: Annotated[Workspace, Depends(get_current_workspace)],
) -> AssetBundle:
    return create_url_asset(payload, workspace)


@router.get("/assets/{asset_id}", response_model=AssetBundle, tags=["assets"])
def asset_detail(
    asset_id: str,
    workspace: Annotated[Workspace, Depends(get_current_workspace)],
) -> AssetBundle:
    bundle = get_asset_bundle(asset_id, workspace)
    if bundle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found.",
        )
    return bundle


@router.get("/assets/{asset_id}/status", response_model=AssetStatusResponse, tags=["assets"])
def asset_status(
    asset_id: str,
    workspace: Annotated[Workspace, Depends(get_current_workspace)],
) -> AssetStatusResponse:
    response = get_asset_status(asset_id, workspace)
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
    workspace: Annotated[Workspace, Depends(get_current_workspace)],
) -> AssetStatusResponse:
    response = process_asset(asset_id, payload, workspace)
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found.",
        )
    return response


@router.get("/admin/assets", response_model=list[AssetBundle], tags=["admin"])
def admin_asset_list(
    _: Annotated[AdminUser, Depends(get_current_admin)],
) -> list[AssetBundle]:
    return list_assets_for_admin()


@router.get(
    "/admin/ingestion/diagnostics",
    response_model=list[IngestionDiagnostic],
    tags=["admin"],
)
def ingestion_diagnostics(
    _: Annotated[AdminUser, Depends(get_current_admin)],
) -> list[IngestionDiagnostic]:
    return list_ingestion_diagnostics()
