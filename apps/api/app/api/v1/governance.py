import json
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.core.config import settings
from app.dependencies.access import WorkspaceAccess, require_admin, require_permission
from app.models.access import AdminUser
from app.services import billing, catalog
from app.services.asset_registry import (
    ARTIFACTS,
    ASSET_SOURCES,
    ASSETS,
    _find_asset,
    _persist_state,
    seed_assets,
)
from app.services.governance import audit, billing_portal, export_json, list_audit, usage, verify_webhook

router = APIRouter()


@router.get("/usage", tags=["governance"])
def workspace_usage(access: Annotated[WorkspaceAccess, Depends(require_permission("usage.read"))]):
    return {"workspace_id": access.workspace.id, "usage": usage(access.workspace.id)}


@router.get("/admin/usage", tags=["admin"])
def all_usage(_: Annotated[AdminUser, Depends(require_admin("admin.support"))]):
    return {workspace.id: usage(workspace.id) for workspace in catalog.WORKSPACES}


@router.post("/billing/portal", tags=["governance"])
def create_billing_portal(
    return_url: str,
    access: Annotated[WorkspaceAccess, Depends(require_permission("billing.manage"))],
):
    """Open the Stripe portal for *this workspace's tenant*; the customer is never client-supplied."""
    customer_id = billing.customer_for_tenant(access.workspace.tenant_id)
    url = billing_portal(customer_id, return_url)
    audit(access.principal.actor, "billing.portal_created", "workspace", access.workspace.id, access.workspace.id)
    return {"url": url}


class LinkCustomerRequest(BaseModel):
    customer_id: str = Field(pattern=r"^cus_[A-Za-z0-9]+$")


@router.put("/admin/tenants/{tenant_id}/billing-customer", status_code=204, tags=["admin"])
def link_billing_customer(
    tenant_id: str,
    payload: LinkCustomerRequest,
    admin: Annotated[AdminUser, Depends(require_admin("admin.operate"))],
):
    if not billing.link_customer(tenant_id, payload.customer_id):
        raise HTTPException(status_code=409, detail="Unknown tenant or customer already linked elsewhere.")
    audit(admin.email, "billing.customer_linked", "tenant", tenant_id, None)


@router.get("/audit-logs", tags=["governance"])
def workspace_audit_logs(access: Annotated[WorkspaceAccess, Depends(require_permission("api_key.manage"))]):
    """Workspace owners may read only their own workspace's audit trail."""
    return list_audit(access.workspace.id)


@router.get("/admin/audit-logs", tags=["admin"])
def audit_logs(_: Annotated[AdminUser, Depends(require_admin("audit.read"))]):
    return list_audit()


@router.get("/assets/{asset_id}/export", tags=["governance"])
def export_asset(asset_id: str, access: Annotated[WorkspaceAccess, Depends(require_permission("assets.export"))]):
    seed_assets()
    asset = _find_asset(asset_id)
    if not asset or asset.workspace_id != access.workspace.id:
        return Response(status_code=404)
    data = {"asset": asset, "artifacts": [item for item in ARTIFACTS if item.asset_id == asset_id]}
    audit(access.principal.actor, "asset.exported", "asset", asset_id, access.workspace.id)
    return Response(export_json(data), media_type="application/json",
                    headers={"Content-Disposition": f'attachment; filename="{asset_id}.json"'})


@router.delete("/assets/{asset_id}", status_code=204, tags=["governance"])
def delete_asset(asset_id: str, access: Annotated[WorkspaceAccess, Depends(require_permission("assets.delete"))]):
    seed_assets()
    asset = _find_asset(asset_id)
    if not asset or asset.workspace_id != access.workspace.id:
        return Response(status_code=404)
    ASSETS[ASSETS.index(asset)] = asset.model_copy(update={
        "status": "deleted", "processing_status": "deleted", "updated_at": datetime.now(timezone.utc).isoformat(),
        "warnings": ["Secure deletion requested; retention policy applies."]})
    for source in [item for item in ASSET_SOURCES if item.asset_id == asset_id]:
        ASSET_SOURCES[ASSET_SOURCES.index(source)] = source.model_copy(
            update={"content_base64": None, "location": "deleted://redacted"})
    _persist_state()
    audit(access.principal.actor, "asset.deletion_requested", "asset", asset_id, access.workspace.id)
    return Response(status_code=204)


@router.post("/admin/retention/run", tags=["admin"])
def run_retention(admin: Annotated[AdminUser, Depends(require_admin("admin.operate"))]):
    """Purge assets past their retention deadline (also runnable as a scheduled job)."""
    from app.services.retention import purge_due_assets

    result = purge_due_assets()
    audit(admin.email, "retention.run", "platform", "retention", None)
    return result


@router.post("/webhooks/{provider}", status_code=202, tags=["webhooks"])
async def webhook(
    provider: str,
    request: Request,
    x_gxrag_signature: Annotated[str | None, Header()] = None,
    stripe_signature: Annotated[str | None, Header()] = None,
):
    body = await request.body()
    if provider == "stripe":
        verify_webhook(body, stripe_signature, settings.stripe_webhook_secret)
    else:
        verify_webhook(body, x_gxrag_signature, settings.webhook_secret)
    try:
        event = json.loads(body)
        event_id = str(event["id"]) if isinstance(event, dict) and event.get("id") else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Webhook body must be JSON.") from None
    if event_id is None:
        raise HTTPException(status_code=400, detail="Webhook event id is required.")
    if not billing.first_delivery(provider, event_id):
        return {"accepted": True, "duplicate": True}
    tenant_id = None
    if provider == "stripe" and isinstance(event.get("data", {}).get("object"), dict):
        customer = event["data"]["object"].get("customer")
        tenant_id = billing.tenant_for_customer(customer) if isinstance(customer, str) else None
    audit(provider, f"webhook.{event.get('type', 'received')}", "tenant" if tenant_id else "webhook", tenant_id or event_id)
    return {"accepted": True, "duplicate": False}
