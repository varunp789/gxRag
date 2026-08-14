from typing import Annotated
from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import Response
from app.dependencies.access import get_current_admin, get_current_workspace
from app.models.access import AdminUser, Workspace
from app.services.governance import AUDIT, audit, billing_portal, export_json, usage, verify_webhook
from app.services.asset_registry import ASSETS, ASSET_SOURCES, ARTIFACTS, _find_asset, _persist_state, seed_assets
from app.core.config import settings

router=APIRouter()
@router.get('/usage', tags=['governance'])
def workspace_usage(workspace:Annotated[Workspace,Depends(get_current_workspace)]): return {'workspace_id':workspace.id,'usage':usage(workspace.id)}
@router.get('/admin/usage', tags=['admin'])
def all_usage(_:Annotated[AdminUser,Depends(get_current_admin)]): return {workspace.id:usage(workspace.id) for workspace in __import__('app.services.catalog',fromlist=['WORKSPACES']).WORKSPACES}
@router.post('/billing/portal', tags=['governance'])
def create_billing_portal(customer_id:str, return_url:str, workspace:Annotated[Workspace,Depends(get_current_workspace)]):
    url=billing_portal(customer_id,return_url); audit('workspace_user','billing.portal_created','workspace',workspace.id); return {'url':url}
@router.get('/admin/audit-logs', tags=['admin'])
def audit_logs(_:Annotated[AdminUser,Depends(get_current_admin)]): return list(reversed(AUDIT))
@router.get('/assets/{asset_id}/export', tags=['governance'])
def export_asset(asset_id:str, workspace:Annotated[Workspace,Depends(get_current_workspace)]):
    seed_assets(); asset=_find_asset(asset_id)
    if not asset or asset.workspace_id!=workspace.id: return Response(status_code=404)
    data={'asset':asset,'artifacts':[item for item in ARTIFACTS if item.asset_id==asset_id]}
    return Response(export_json(data), media_type='application/json', headers={'Content-Disposition':f'attachment; filename="{asset_id}.json"'})
@router.delete('/assets/{asset_id}', status_code=204, tags=['governance'])
def delete_asset(asset_id:str, workspace:Annotated[Workspace,Depends(get_current_workspace)]):
    seed_assets(); asset=_find_asset(asset_id)
    if not asset or asset.workspace_id!=workspace.id: return Response(status_code=404)
    ASSETS[ASSETS.index(asset)]=asset.model_copy(update={'status':'deleted','processing_status':'deleted','warnings':['Secure deletion requested; retention policy applies.']})
    for source in [item for item in ASSET_SOURCES if item.asset_id == asset_id]:
        ASSET_SOURCES[ASSET_SOURCES.index(source)] = source.model_copy(update={'content_base64': None, 'location': 'deleted://redacted'})
    _persist_state(); audit('workspace_user','asset.deletion_requested','asset',asset_id); return Response(status_code=204)
@router.post('/webhooks/{provider}', status_code=202, tags=['webhooks'])
async def webhook(provider:str, request:Request, x_gxrag_signature:Annotated[str|None,Header()]=None):
    body=await request.body(); verify_webhook(body,x_gxrag_signature,settings.webhook_secret); audit(provider,'webhook.received','webhook',provider); return {'accepted':True}
