from app.models.access import (
    AccessOverview,
    AdminUser,
    ApiKey,
    AuditLog,
    Permission,
    Plan,
    Role,
    Tenant,
    User,
    Workspace,
    WorkspaceMember,
    WorkspaceScope,
)
from app.models.product import (
    AdminCapability,
    ApiEndpointGroup,
    AssetOutputContract,
    ProductDefinition,
    ProductPackaging,
    QueryContract,
    RetrievalMode,
    SourceType,
    UsageUnit,
)

PLANS = [
    Plan(
        id="plan_starter",
        name="Starter",
        monthly_document_limit=100,
        monthly_query_limit=2500,
        max_workspace_members=5,
    ),
    Plan(
        id="plan_growth",
        name="Growth",
        monthly_document_limit=1000,
        monthly_query_limit=25000,
        max_workspace_members=25,
    ),
]

_PERMISSION_DESCRIPTIONS = {
    "workspace.read": "Read workspace configuration and metadata.",
    "assets.read": "List assets and read their status and artifacts.",
    "assets.write": "Upload, register and process assets.",
    "assets.delete": "Request deletion of assets.",
    "assets.export": "Export asset data.",
    "query.run": "Run retrieval and hosted-answer queries.",
    "usage.read": "Read workspace usage and quota consumption.",
    "api_key.manage": "Create and revoke API keys for a workspace.",
    "billing.manage": "Open the billing portal for a workspace.",
    "admin.support": "Perform support and inspection actions in the admin portal.",
    "admin.operate": "Retry jobs and trigger index reconciliation.",
    "audit.read": "Read the audit log.",
}

PERMISSIONS = [
    Permission(id="perm_" + name.replace(".", "_"), name=name, description=description)
    for name, description in _PERMISSION_DESCRIPTIONS.items()
]


def _perm_ids(*names: str) -> list[str]:
    return ["perm_" + name.replace(".", "_") for name in names]


_WORKSPACE_ALL = ("workspace.read", "assets.read", "assets.write", "assets.delete",
                  "assets.export", "query.run", "usage.read", "api_key.manage", "billing.manage")

ROLES = [
    Role(id="role_workspace_owner", name="workspace_owner", permission_ids=_perm_ids(*_WORKSPACE_ALL)),
    Role(id="role_analyst", name="analyst",
         permission_ids=_perm_ids("workspace.read", "assets.read", "query.run", "usage.read")),
    Role(id="role_ingestion_writer", name="ingestion_writer",
         permission_ids=_perm_ids("assets.read", "assets.write")),
    Role(id="role_retrieval_reader", name="retrieval_reader",
         permission_ids=_perm_ids("assets.read", "query.run")),
    Role(id="role_support_admin", name="support_admin", permission_ids=_perm_ids("admin.support")),
    Role(id="role_platform_admin", name="platform_admin",
         permission_ids=_perm_ids("admin.support", "admin.operate", "audit.read")),
]


def permissions_for_roles(role_names: list[str] | tuple[str, ...]) -> set[str]:
    """Resolve role names to permission names (unknown roles grant nothing)."""
    by_id = {permission.id: permission.name for permission in PERMISSIONS}
    return {
        by_id[permission_id]
        for role in ROLES if role.name in role_names
        for permission_id in role.permission_ids
    }


TENANTS = [
    Tenant(
        id="tenant_orbit",
        name="Orbit Bio Labs",
        slug="orbit-bio-labs",
        plan_id="plan_growth",
        status="active",
    ),
    Tenant(
        id="tenant_rivet",
        name="Rivet Capital",
        slug="rivet-capital",
        plan_id="plan_starter",
        status="trial",
    ),
]

WORKSPACES = [
    Workspace(
        id="ws_orbit_prod",
        tenant_id="tenant_orbit",
        name="Orbit Production",
        slug="orbit-production",
        environment="production",
        region="us-east-1",
        status="active",
    ),
    Workspace(
        id="ws_orbit_research",
        tenant_id="tenant_orbit",
        name="Orbit Research",
        slug="orbit-research",
        environment="staging",
        region="us-east-1",
        status="active",
    ),
    Workspace(
        id="ws_rivet_trial",
        tenant_id="tenant_rivet",
        name="Rivet Trial Workspace",
        slug="rivet-trial",
        environment="production",
        region="eu-west-1",
        status="active",
    ),
]

USERS = [
    User(
        id="user_alex",
        email="alex@orbit.bio",
        full_name="Alex Mercer",
        roles=["workspace_owner"],
        workspace_ids=["ws_orbit_prod", "ws_orbit_research"],
    ),
    User(
        id="user_sam",
        email="sam@orbit.bio",
        full_name="Sam Rivera",
        roles=["analyst"],
        workspace_ids=["ws_orbit_prod"],
    ),
    User(
        id="user_nia",
        email="nia@rivet.capital",
        full_name="Nia Patel",
        roles=["workspace_owner"],
        workspace_ids=["ws_rivet_trial"],
    ),
]

ADMIN_USERS = [
    AdminUser(
        id="admin_ops",
        email="ops@gxrag.dev",
        full_name="Platform Ops",
        roles=["platform_admin", "support_admin"],
    )
]

WORKSPACE_MEMBERS = [
    WorkspaceMember(
        id="wm_1",
        workspace_id="ws_orbit_prod",
        user_id="user_alex",
        role="workspace_owner",
        status="active",
    ),
    WorkspaceMember(
        id="wm_2",
        workspace_id="ws_orbit_research",
        user_id="user_alex",
        role="workspace_owner",
        status="active",
    ),
    WorkspaceMember(
        id="wm_3",
        workspace_id="ws_orbit_prod",
        user_id="user_sam",
        role="analyst",
        status="active",
    ),
    WorkspaceMember(
        id="wm_4",
        workspace_id="ws_rivet_trial",
        user_id="user_nia",
        role="workspace_owner",
        status="active",
    ),
]

API_KEYS = [
    ApiKey(
        id="key_orbit_prod",
        workspace_id="ws_orbit_prod",
        name="Orbit production ingestion",
        prefix="gxr_prod_1",
        role="ingestion_writer",
        status="active",
    ),
    ApiKey(
        id="key_orbit_research",
        workspace_id="ws_orbit_research",
        name="Orbit research explorer",
        prefix="gxr_stage_1",
        role="retrieval_reader",
        status="active",
    ),
    ApiKey(
        id="key_rivet_trial",
        workspace_id="ws_rivet_trial",
        name="Rivet trial SDK key",
        prefix="gxr_trial_1",
        role="workspace_owner",
        status="active",
    ),
]

AUDIT_LOGS = [
    AuditLog(
        id="audit_1",
        actor_email="ops@gxrag.dev",
        action="tenant.reviewed",
        resource_type="tenant",
        resource_id="tenant_orbit",
        occurred_at="2026-08-13T09:00:00Z",
    ),
    AuditLog(
        id="audit_2",
        actor_email="alex@orbit.bio",
        action="workspace.api_key.created",
        resource_type="workspace",
        resource_id="ws_orbit_prod",
        occurred_at="2026-08-13T09:20:00Z",
    ),
]

PRODUCT_DEFINITION = ProductDefinition(
    packaging=[
        ProductPackaging(
            sku="api_starter",
            name="API Starter",
            audience="teams embedding Graph RAG into their own apps",
            billing_unit="documents + queries",
        ),
        ProductPackaging(
            sku="hosted_workspace",
            name="Hosted Workspace",
            audience="teams using the client portal and managed retrieval",
            billing_unit="workspaces + usage",
        ),
        ProductPackaging(
            sku="enterprise",
            name="Enterprise",
            audience="large customers requiring admin controls and advanced governance",
            billing_unit="contracted capacity",
        ),
    ],
    usage_units=[
        UsageUnit(
            key="document",
            label="Documents processed",
            description="Charged for each uploaded file or connected document processed.",
        ),
        UsageUnit(
            key="page",
            label="Pages processed",
            description="Used for PDFs, images, and OCR-heavy workflows.",
        ),
        UsageUnit(
            key="query",
            label="Queries executed",
            description="Counts retrieval and answer-generation requests.",
        ),
        UsageUnit(
            key="token",
            label="Hosted LLM tokens",
            description="Applied only when the platform generates the final answer.",
        ),
    ],
    source_types=[
        SourceType(key="pdf", label="PDF", enabled_in_v1=True),
        SourceType(key="csv_excel", label="CSV / Excel", enabled_in_v1=True),
        SourceType(key="web", label="Web content", enabled_in_v1=True),
        SourceType(key="image", label="Image", enabled_in_v1=False),
        SourceType(key="audio", label="Audio", enabled_in_v1=False),
    ],
    retrieval_modes=[
        RetrievalMode(key="vector", label="Vector retrieval", enabled_in_v1=True),
        RetrievalMode(key="hybrid", label="Hybrid retrieval", enabled_in_v1=True),
        RetrievalMode(key="graph", label="Graph retrieval", enabled_in_v1=True),
        RetrievalMode(
            key="multimodal",
            label="Multimodal retrieval",
            enabled_in_v1=False,
        ),
    ],
    admin_capabilities=[
        AdminCapability(key="tenant_admin", label="Tenant and plan management"),
        AdminCapability(key="job_ops", label="Job monitoring and retries"),
        AdminCapability(key="audit_ops", label="Audit and support workflows"),
    ],
    output_contract=AssetOutputContract(
        fields=[
            "workspace_id",
            "asset_id",
            "document_id",
            "table_id",
            "artifact_refs",
            "graph_refs",
            "vector_index_refs",
            "keyword_index_refs",
            "provenance",
        ]
    ),
    query_contract=QueryContract(
        request_fields=[
            "workspace_id",
            "asset_id",
            "query",
            "retrieval_mode",
            "filters",
            "limit",
        ],
        response_fields=[
            "results",
            "citations",
            "scores",
            "graph_paths",
            "table_refs",
            "provenance",
        ],
        retrieval_modes=["vector", "hybrid", "graph"],
    ),
    versioning_policy="All customer APIs live under /v1 until a breaking change requires /v2.",
    compatibility_policy="Additive changes are allowed within a major version; breaking changes require a new version and migration notice.",
    endpoint_groups=[
        ApiEndpointGroup(
            name="Platform metadata",
            endpoints=["GET /v1/platform/definition", "GET /v1/platform/api-scope"],
        ),
        ApiEndpointGroup(
            name="Access foundation",
            endpoints=[
                "GET /v1/access/overview",
                "GET /v1/workspaces",
                "GET /v1/workspaces/current",
                "GET /v1/admin/tenants",
                "GET /v1/admin/workspaces/{workspace_id}",
            ],
        ),
        ApiEndpointGroup(
            name="Planned ingestion surface",
            endpoints=[
                "POST /v1/assets/upload",
                "POST /v1/assets/{id}/process",
                "GET /v1/assets/{id}/status",
            ],
        ),
    ],
)


def get_product_definition() -> ProductDefinition:
    return PRODUCT_DEFINITION


def get_access_overview() -> AccessOverview:
    return AccessOverview(
        plans=PLANS,
        permissions=PERMISSIONS,
        roles=ROLES,
        tenants=TENANTS,
        workspaces=WORKSPACES,
        users=USERS,
        admin_users=ADMIN_USERS,
        workspace_members=WORKSPACE_MEMBERS,
        api_keys=API_KEYS,
        audit_logs=AUDIT_LOGS,
    )


def get_user_by_email(email: str) -> User | None:
    return next((user for user in USERS if user.email == email), None)


def get_admin_by_email(email: str) -> AdminUser | None:
    return next((user for user in ADMIN_USERS if user.email == email), None)


def list_workspaces_for_user(email: str) -> list[Workspace]:
    user = get_user_by_email(email)
    if user is None:
        return []
    return [workspace for workspace in WORKSPACES if workspace.id in user.workspace_ids]


def get_workspace(workspace_id: str) -> Workspace | None:
    return next((workspace for workspace in WORKSPACES if workspace.id == workspace_id), None)


def get_tenant(tenant_id: str) -> Tenant | None:
    return next((tenant for tenant in TENANTS if tenant.id == tenant_id), None)


def get_workspace_scope(workspace_id: str) -> WorkspaceScope | None:
    workspace = get_workspace(workspace_id)
    if workspace is None:
        return None
    tenant = get_tenant(workspace.tenant_id)
    if tenant is None:
        return None
    return WorkspaceScope(
        workspace=workspace,
        tenant=tenant,
        memberships=[
            member for member in WORKSPACE_MEMBERS if member.workspace_id == workspace_id
        ],
        api_keys=[key for key in API_KEYS if key.workspace_id == workspace_id],
    )


def get_membership(user_id: str, workspace_id: str) -> WorkspaceMember | None:
    return next(
        (member for member in WORKSPACE_MEMBERS
         if member.user_id == user_id and member.workspace_id == workspace_id
         and member.status == "active"),
        None,
    )
