from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies.access import (
    get_current_admin,
    get_current_user,
    get_current_workspace,
)
from app.models.access import AccessOverview, AdminUser, User, Workspace, WorkspaceScope
from app.services.catalog import (
    get_access_overview,
    get_tenant,
    get_workspace_scope,
    list_workspaces_for_user,
)

router = APIRouter()


@router.get("/access/overview", response_model=AccessOverview, tags=["access"])
def access_overview(
    _: Annotated[AdminUser, Depends(get_current_admin)],
) -> AccessOverview:
    return get_access_overview()


@router.get("/workspaces", response_model=list[Workspace], tags=["workspaces"])
def list_workspaces(
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[Workspace]:
    return list_workspaces_for_user(current_user.email)


@router.get("/workspaces/current", response_model=WorkspaceScope, tags=["workspaces"])
def current_workspace(
    workspace: Annotated[Workspace, Depends(get_current_workspace)],
) -> WorkspaceScope:
    scope = get_workspace_scope(workspace.id)
    if scope is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace scope not found.",
        )
    return scope


@router.get("/admin/tenants", tags=["admin"])
def list_tenants(
    _: Annotated[AdminUser, Depends(get_current_admin)],
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
    _: Annotated[AdminUser, Depends(get_current_admin)],
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
    _: Annotated[AdminUser, Depends(get_current_admin)],
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
