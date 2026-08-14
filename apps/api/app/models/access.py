from pydantic import BaseModel, Field


class Plan(BaseModel):
    id: str
    name: str
    monthly_document_limit: int
    monthly_query_limit: int
    max_workspace_members: int


class Permission(BaseModel):
    id: str
    name: str
    description: str


class Role(BaseModel):
    id: str
    name: str
    permission_ids: list[str] = Field(default_factory=list)


class Tenant(BaseModel):
    id: str
    name: str
    slug: str
    plan_id: str
    status: str


class Workspace(BaseModel):
    id: str
    tenant_id: str
    name: str
    slug: str
    environment: str
    region: str
    status: str


class User(BaseModel):
    id: str
    email: str
    full_name: str
    roles: list[str] = Field(default_factory=list)
    workspace_ids: list[str] = Field(default_factory=list)


class AdminUser(BaseModel):
    id: str
    email: str
    full_name: str
    roles: list[str] = Field(default_factory=list)


class WorkspaceMember(BaseModel):
    id: str
    workspace_id: str
    user_id: str
    role: str
    status: str


class ApiKey(BaseModel):
    id: str
    workspace_id: str
    name: str
    prefix: str
    role: str
    status: str


class AuditLog(BaseModel):
    id: str
    actor_email: str
    action: str
    resource_type: str
    resource_id: str
    occurred_at: str


class AccessOverview(BaseModel):
    plans: list[Plan]
    permissions: list[Permission]
    roles: list[Role]
    tenants: list[Tenant]
    workspaces: list[Workspace]
    users: list[User]
    admin_users: list[AdminUser]
    workspace_members: list[WorkspaceMember]
    api_keys: list[ApiKey]
    audit_logs: list[AuditLog]


class WorkspaceScope(BaseModel):
    workspace: Workspace
    tenant: Tenant
    memberships: list[WorkspaceMember]
    api_keys: list[ApiKey]
