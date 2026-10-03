from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from pydantic import BaseModel

from app.dependencies.access import (
    WorkspaceAccess,
    get_current_user,
    require_admin,
    require_permission,
)
from app.models.access import AccessOverview, AdminUser, ApiKey, User, Workspace, WorkspaceScope
from app.services import api_keys
from app.services.governance import audit
from app.services.catalog import (
    get_access_overview,
    get_tenant,
    get_workspace_scope,
    list_workspaces_for_user,
)

router = APIRouter()


@router.get("/access/overview", response_model=AccessOverview, tags=["access"])
def access_overview(
    _: Annotated[AdminUser, Depends(require_admin("admin.support"))],
) -> AccessOverview:
    return get_access_overview()


@router.get("/workspaces", response_model=list[Workspace], tags=["workspaces"])
def list_workspaces(
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[Workspace]:
    return list_workspaces_for_user(current_user.email)


@router.get("/workspaces/current", response_model=WorkspaceScope, tags=["workspaces"])
def current_workspace(
    access: Annotated[WorkspaceAccess, Depends(require_permission("workspace.read"))],
) -> WorkspaceScope:
    scope = get_workspace_scope(access.workspace.id)
    if scope is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace scope not found.",
        )
    return scope


@router.get("/admin/tenants", tags=["admin"])
def list_tenants(
    _: Annotated[AdminUser, Depends(require_admin("admin.support"))],
) -> dict[str, list[dict[str, str]]]:
    overview = get_access_overview()
    return {
        "tenants": [
            {
                "id": tenant.id,
                "name": tenant.name,
                "slug": tenant.slug,
                "plan_id": tenant.plan_id,
                "status": tenant.status,
            }
            for tenant in overview.tenants
        ]
    }


@router.get(
    "/admin/workspaces/{workspace_id}",
    response_model=WorkspaceScope,
    tags=["admin"],
)
def admin_workspace_detail(
    workspace_id: str,
    _: Annotated[AdminUser, Depends(require_admin("admin.support"))],
) -> WorkspaceScope:
    scope = get_workspace_scope(workspace_id)
    if scope is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found.",
        )
    return scope


@router.get("/admin/tenants/{tenant_id}", tags=["admin"])
def admin_tenant_detail(
    tenant_id: str,
    _: Annotated[AdminUser, Depends(require_admin("admin.support"))],
) -> dict[str, object]:
    overview = get_access_overview()
    tenant = get_tenant(tenant_id)
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found.",
        )
    return {
        "tenant": tenant.model_dump(),
        "workspaces": [
            workspace.model_dump()
            for workspace in overview.workspaces
            if workspace.tenant_id == tenant_id
        ],
    }


class CreateApiKeyRequest(BaseModel):
    name: str
    role: str = "retrieval_reader"


class CreatedApiKey(BaseModel):
    key: ApiKey
    secret: str


_KEY_ROLES = {"ingestion_writer", "retrieval_reader"}


@router.get("/api-keys", response_model=list[ApiKey], tags=["api-keys"])
def list_api_keys(
    access: Annotated[WorkspaceAccess, Depends(require_permission("api_key.manage"))],
) -> list[ApiKey]:
    return api_keys.list_keys(access.workspace.id)


@router.post("/api-keys", response_model=CreatedApiKey, status_code=201, tags=["api-keys"])
def create_api_key(
    payload: CreateApiKeyRequest,
    access: Annotated[WorkspaceAccess, Depends(require_permission("api_key.manage"))],
) -> CreatedApiKey:
    # Machine keys never receive management or billing permissions.
    if payload.role not in _KEY_ROLES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"API key role must be one of {sorted(_KEY_ROLES)}.")
    key, secret = api_keys.create_key(access.workspace.id, payload.name, payload.role)
    audit(access.principal.actor, "api_key.created", "api_key", key.id, access.workspace.id)
    return CreatedApiKey(key=key, secret=secret)


@router.delete("/api-keys/{key_id}", status_code=204, tags=["api-keys"])
def revoke_api_key(
    key_id: str,
    access: Annotated[WorkspaceAccess, Depends(require_permission("api_key.manage"))],
) -> None:
    if not api_keys.revoke_key(access.workspace.id, key_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found.")
    audit(access.principal.actor, "api_key.revoked", "api_key", key_id, access.workspace.id)
