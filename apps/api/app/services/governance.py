"""Phase 11 control plane: quotas, metering, audit records, retention and webhooks."""
from __future__ import annotations
import hashlib, hmac, json
from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock
from fastapi import HTTPException, Request, status
import httpx
from app.core.config import settings
from app.services.catalog import PLANS, TENANTS, WORKSPACES

_lock=Lock(); USAGE: dict[str, dict[str,int]]=defaultdict(lambda: defaultdict(int)); AUDIT: list[dict[str,str]]=[]; RATE: dict[str,list[float]]=defaultdict(list)

def now()->str: return datetime.now(timezone.utc).isoformat()
def record(workspace_id:str, unit:str, count:int=1)->None:
    with _lock: USAGE[workspace_id][unit]+=count
def usage(workspace_id:str)->dict[str,int]: return dict(USAGE[workspace_id])
def audit(actor:str, action:str, resource_type:str, resource_id:str)->None: AUDIT.append({"actor":actor,"action":action,"resource_type":resource_type,"resource_id":resource_id,"occurred_at":now()})
def enforce_quota(workspace_id:str, unit:str)->None:
    workspace=next(item for item in WORKSPACES if item.id==workspace_id); plan=next(item for item in PLANS if item.id==next(tenant.plan_id for tenant in TENANTS if tenant.id==workspace.tenant_id)); limit=plan.monthly_document_limit if unit=="document" else plan.monthly_query_limit
    if usage(workspace_id).get(unit,0)>=limit: raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,detail=f"{unit} quota exceeded.")
def rate_limit(request:Request, limit:int=120)->None:
    import time
    key=request.headers.get("x-actor-email",request.client.host if request.client else "anonymous"); current=time.time()
    with _lock:
        values=[item for item in RATE[key] if item>current-60]; values.append(current); RATE[key]=values
        if len(values)>limit: raise HTTPException(status_code=429,detail="Rate limit exceeded.")
def verify_webhook(payload:bytes, signature:str|None, secret:str|None)->None:
    if not secret or not signature: raise HTTPException(status_code=401,detail="Webhook signature required.")
    expected=hmac.new(secret.encode(),payload,hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected,signature): raise HTTPException(status_code=401,detail="Invalid webhook signature.")
def export_json(value:object)->str: return json.dumps(value, default=lambda item: item.model_dump() if hasattr(item,"model_dump") else str(item))
def billing_portal(customer_id:str, return_url:str)->str:
    if not settings.stripe_secret_key: raise HTTPException(status_code=503,detail="Stripe billing is not configured.")
    response=httpx.post("https://api.stripe.com/v1/billing_portal/sessions",headers={"Authorization":f"Bearer {settings.stripe_secret_key}"},data={"customer":customer_id,"return_url":return_url},timeout=20)
    response.raise_for_status(); return response.json()["url"]
