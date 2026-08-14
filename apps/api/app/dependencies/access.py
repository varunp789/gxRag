from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.models.access import AdminUser, User, Workspace
from app.services.catalog import (
    get_admin_by_email,
    get_workspace,
    get_user_by_email,
    list_workspaces_for_user,
)


def get_current_user(
    x_actor_email: Annotated[str | None, Header()] = None,
) -> User:
    email = x_actor_email or "alex@orbit.bio"
    user = get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unknown workspace user.",
        )
    return user


def get_current_admin(
    x_admin_email: Annotated[str | None, Header()] = None,
) -> AdminUser:
    email = x_admin_email or "ops@gxrag.dev"
    admin = get_admin_by_email(email)
    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unknown admin user.",
        )
    return admin


def get_current_workspace(
    current_user: Annotated[User, Depends(get_current_user)],
    x_workspace_id: Annotated[str | None, Header()] = None,
) -> Workspace:
    available_workspaces = list_workspaces_for_user(current_user.email)
    if not available_workspaces:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No workspace access found for the current user.",
        )

    if x_workspace_id is None:
        return available_workspaces[0]

    workspace = get_workspace(x_workspace_id)
    if workspace is None or workspace.id not in current_user.workspace_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workspace access denied.",
        )
    return workspace

