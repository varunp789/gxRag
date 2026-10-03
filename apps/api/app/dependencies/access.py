"""Authentication, workspace scoping and RBAC enforcement.

``dev`` auth mode trusts ``X-Actor-Email`` / ``X-Admin-Email`` headers and exists
only for local work (``Settings.validate_for_runtime`` rejects it elsewhere).
``jwt`` mode requires ``Authorization: Bearer`` carrying either a signed user or
admin token, or a workspace API key (``gxk_<prefix>_<secret>``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Callable

from fastapi import Depends, Header, HTTPException, status

from app.core.config import settings
from app.core.security import TokenError, decode_token
from app.models.access import AdminUser, User, Workspace
from app.services import api_keys
from app.services.catalog import (
    get_admin_by_email,
    get_membership,
    get_user_by_email,
    get_workspace,
    permissions_for_roles,
)


@dataclass(frozen=True)
class Principal:
    kind: str  # "user" | "admin" | "api_key"
    subject: str
    email: str | None = None
    api_key_workspace_id: str | None = None
    api_key_role: str | None = None

    @property
    def actor(self) -> str:
        return self.email or f"api_key:{self.subject}"


@dataclass(frozen=True)
class WorkspaceAccess:
    workspace: Workspace
    principal: Principal
    permissions: frozenset[str]


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail,
                         headers={"WWW-Authenticate": "Bearer"})


def _bearer(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise _unauthorized("Authentication required.")
    return authorization[7:].strip()


def get_principal(
    authorization: Annotated[str | None, Header()] = None,
    x_actor_email: Annotated[str | None, Header()] = None,
) -> Principal:
    if settings.auth_mode == "dev":
        email = x_actor_email or "alex@orbit.bio"
        return Principal(kind="user", subject=email, email=email)

    token = _bearer(authorization)
    if token.startswith("gxk_"):
        key = api_keys.authenticate_key(token)
        if key is None:
            raise _unauthorized("Invalid API key.")
        return Principal(kind="api_key", subject=key.id, api_key_workspace_id=key.workspace_id,
                         api_key_role=key.role)
    try:
        claims = decode_token(token)
    except TokenError as error:
        raise _unauthorized(str(error)) from error
    kind = "admin" if claims.get("typ") == "admin" else "user"
    return Principal(kind=kind, subject=str(claims["sub"]), email=str(claims["email"]).lower())


def get_current_user(principal: Annotated[Principal, Depends(get_principal)]) -> User:
    if principal.kind != "user":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="A user identity is required.")
    user = get_user_by_email(principal.email or "")
    if user is None:
        raise _unauthorized("Unknown workspace user.")
    return user


def get_current_admin(
    authorization: Annotated[str | None, Header()] = None,
    x_admin_email: Annotated[str | None, Header()] = None,
) -> AdminUser:
    if settings.auth_mode == "dev":
        email = x_admin_email or "ops@gxrag.dev"
    else:
        token = _bearer(authorization)
        try:
            claims = decode_token(token) if not token.startswith("gxk_") else None
        except TokenError as error:
            raise _unauthorized(str(error)) from error
        if claims is None or claims.get("typ") != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator access required.")
        email = str(claims["email"]).lower()
    admin = get_admin_by_email(email)
    if admin is None:
        raise _unauthorized("Unknown admin user.")
    return admin


def require_admin(permission: str) -> Callable[..., AdminUser]:
    """Dependency factory: admin identity holding ``permission``."""

    def dependency(
        admin: Annotated[AdminUser, Depends(get_current_admin)],
    ) -> AdminUser:
        if permission not in permissions_for_roles(admin.roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"Missing permission: {permission}.")
        return admin

    return dependency


def _resolve_workspace_access(principal: Principal, workspace_id: str | None) -> WorkspaceAccess:
    if principal.kind == "api_key":
        # A key is bound to exactly one workspace; a header may not retarget it.
        bound = principal.api_key_workspace_id
        if workspace_id and workspace_id != bound:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace access denied.")
        workspace = get_workspace(bound or "")
        if workspace is None or workspace.status != "active":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace access denied.")
        return WorkspaceAccess(workspace, principal, frozenset(permissions_for_roles([principal.api_key_role or ""])))

    if principal.kind != "user":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="A workspace identity is required.")
    user = get_user_by_email(principal.email or "")
    if user is None:
        raise _unauthorized("Unknown workspace user.")
    candidates = [wid for wid in user.workspace_ids if get_membership(user.id, wid)]
    if not candidates:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="No workspace access found for the current user.")
    target = workspace_id or candidates[0]
    membership = get_membership(user.id, target)
    workspace = get_workspace(target)
    if membership is None or workspace is None or workspace.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace access denied.")
    return WorkspaceAccess(workspace, principal, frozenset(permissions_for_roles([membership.role])))


def require_permission(permission: str) -> Callable[..., WorkspaceAccess]:
    """Dependency factory: scoped workspace access holding ``permission``."""

    def dependency(
        principal: Annotated[Principal, Depends(get_principal)],
        x_workspace_id: Annotated[str | None, Header()] = None,
    ) -> WorkspaceAccess:
        access = _resolve_workspace_access(principal, x_workspace_id)
        if permission not in access.permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"Missing permission: {permission}.")
        return access

    return dependency


def get_current_workspace(
    principal: Annotated[Principal, Depends(get_principal)],
    x_workspace_id: Annotated[str | None, Header()] = None,
) -> Workspace:
    """Workspace for the caller, requiring only membership (``workspace.read``)."""
    access = _resolve_workspace_access(principal, x_workspace_id)
    if "workspace.read" not in access.permissions and principal.kind != "api_key":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing permission: workspace.read.")
    return access.workspace
