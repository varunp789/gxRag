"""Phase 11 control plane: quotas, metering, audit records, retention and webhooks."""
from __future__ import annotations

import hashlib
import hmac
import json
from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock

import httpx
from fastapi import HTTPException, Request, status

from app.core.config import settings
from app.db import store as db_store
from app.services.catalog import PLANS, TENANTS, WORKSPACES

_lock=Lock(); USAGE: dict[str, dict[str,int]]=defaultdict(lambda: defaultdict(int)); AUDIT: list[dict[str,str]]=[]; RATE: dict[str,list[float]]=defaultdict(list)
_USAGE_PERIOD: list[str]=[db_store.current_period()]

def now()->str: return datetime.now(timezone.utc).isoformat()
def _roll_usage_period()->None:
    """Quotas are monthly: reset the in-memory counters when the month changes."""
    period=db_store.current_period()
    if _USAGE_PERIOD[0]!=period: USAGE.clear(); _USAGE_PERIOD[0]=period
def record(workspace_id:str, unit:str, count:int=1)->None:
    if db_store.enabled(): db_store.increment_usage(workspace_id,unit,count); return
    with _lock: _roll_usage_period(); USAGE[workspace_id][unit]+=count
def usage(workspace_id:str)->dict[str,int]:
    if db_store.enabled(): return db_store.read_usage(workspace_id)
    with _lock: _roll_usage_period(); return dict(USAGE[workspace_id])
def audit(actor:str, action:str, resource_type:str, resource_id:str, workspace_id:str|None=None)->None:
    if db_store.enabled(): db_store.insert_audit(actor,action,resource_type,resource_id,workspace_id); return
    AUDIT.append({"actor":actor,"action":action,"resource_type":resource_type,"resource_id":resource_id,"workspace_id":workspace_id or "","occurred_at":now()})
def list_audit(workspace_id:str|None=None, limit:int=200)->list[dict[str,str]]:
    if db_store.enabled(): return db_store.read_audit(workspace_id,limit)
    rows=[row for row in reversed(AUDIT) if workspace_id is None or row.get("workspace_id")==workspace_id]
    return rows[:limit]
def enforce_quota(workspace_id:str, unit:str)->None:
    workspace=next(item for item in WORKSPACES if item.id==workspace_id); plan=next(item for item in PLANS if item.id==next(tenant.plan_id for tenant in TENANTS if tenant.id==workspace.tenant_id)); limit=plan.monthly_document_limit if unit=="document" else plan.monthly_query_limit
    if usage(workspace_id).get(unit,0)>=limit: raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,detail=f"{unit} quota exceeded.")
def rate_limit(request:Request, limit:int|None=None)->None:
    """Sliding-window limiter keyed by credential (hashed) or client address.

    Runs before authentication, so keys are bounded: stale entries are pruned and
    the table is capped to stop random tokens from exhausting memory.
    """
    import time
    limit=limit or settings.rate_limit_per_minute
    credential=request.headers.get("authorization") or request.headers.get("x-actor-email")
    key=hashlib.sha256(credential.encode()).hexdigest()[:16] if credential else (request.client.host if request.client else "anonymous")
    current=time.time()
    with _lock:
        if len(RATE)>10_000:
            for stale in [name for name,values in RATE.items() if not values or values[-1]<=current-60]: del RATE[stale]
            if len(RATE)>10_000 and key not in RATE: raise HTTPException(status_code=429,detail="Rate limit exceeded.")
        values=[item for item in RATE[key] if item>current-60]; values.append(current); RATE[key]=values
        if len(values)>limit: raise HTTPException(status_code=429,detail="Rate limit exceeded.")
WEBHOOK_TOLERANCE_SECONDS=300
def verify_webhook(payload:bytes, signature:str|None, secret:str|None, now_ts:float|None=None)->str:
    """Verify a ``t=<unix>,v1=<hex>`` signature over ``<t>.<payload>`` (Stripe-compatible).

    Rejects stale timestamps so a captured request cannot be replayed later.
    Returns the signed timestamp.
    """
    import time
    if not secret or not signature: raise HTTPException(status_code=401,detail="Webhook signature required.")
    parts=[item.split("=",1) for item in signature.split(",") if "=" in item]
    timestamp=next((value for key,value in parts if key=="t"),None); candidates=[value for key,value in parts if key=="v1"]
    if not timestamp or not candidates or not timestamp.isdigit(): raise HTTPException(status_code=401,detail="Invalid webhook signature.")
    expected=hmac.new(secret.encode(),f"{timestamp}.".encode()+payload,hashlib.sha256).hexdigest()
    if not any(hmac.compare_digest(expected,candidate) for candidate in candidates): raise HTTPException(status_code=401,detail="Invalid webhook signature.")
    if abs((now_ts if now_ts is not None else time.time())-int(timestamp))>WEBHOOK_TOLERANCE_SECONDS: raise HTTPException(status_code=401,detail="Webhook timestamp outside tolerance.")
    return timestamp
def sign_webhook(payload:bytes, secret:str, timestamp:int|None=None)->str:
    import time
    ts=str(timestamp if timestamp is not None else int(time.time()))
    return f"t={ts},v1="+hmac.new(secret.encode(),f"{ts}.".encode()+payload,hashlib.sha256).hexdigest()
def export_json(value:object)->str: return json.dumps(value, default=lambda item: item.model_dump() if hasattr(item,"model_dump") else str(item))
def _return_url_allowed(return_url:str)->bool:
    from urllib.parse import urlparse
    parsed=urlparse(return_url); origin=f"{parsed.scheme}://{parsed.netloc}"
    return parsed.scheme in {"https","http"} and origin in settings.billing_return_origins
def billing_portal(customer_id:str|None, return_url:str)->str:
    if not settings.stripe_secret_key: raise HTTPException(status_code=503,detail="Stripe billing is not configured.")
    if not customer_id: raise HTTPException(status_code=409,detail="No billing customer is linked to this tenant.")
    if not _return_url_allowed(return_url): raise HTTPException(status_code=422,detail="return_url origin is not allowed.")
    response=httpx.post("https://api.stripe.com/v1/billing_portal/sessions",headers={"Authorization":f"Bearer {settings.stripe_secret_key}"},data={"customer":customer_id,"return_url":return_url},timeout=20)
    response.raise_for_status(); return response.json()["url"]
