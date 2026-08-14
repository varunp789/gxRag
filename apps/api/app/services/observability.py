"""Structured telemetry and operational diagnostics shared by API and workers."""
from __future__ import annotations
import json, logging, time
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from app.core.config import settings

trace_id: ContextVar[str] = ContextVar("trace_id", default="")
logger=logging.getLogger("gxrag")
if not logger.handlers:
    handler=logging.StreamHandler(); handler.setFormatter(logging.Formatter("%(message)s")); logger.addHandler(handler); logger.setLevel(logging.INFO)
def utc_now()->str: return datetime.now(timezone.utc).isoformat()
def emit(event:str, **fields:object)->None: logger.info(json.dumps({"timestamp":utc_now(),"event":event,"trace_id":trace_id.get(),**fields},default=str))
def timed(event:str):
    def decorate(fn):
        def wrapped(*args,**kwargs):
            started=time.perf_counter()
            try: return fn(*args,**kwargs)
            finally: emit(event,duration_ms=round((time.perf_counter()-started)*1000,2))
        return wrapped
    return decorate
def artifact_integrity() -> list[dict[str,str]]:
    root=Path(settings.artifact_root); issues=[]
    if not root.exists(): return [{"severity":"warning","message":"Artifact root does not yet exist."}]
    for asset_path in root.glob("*/*"):
        if asset_path.is_dir() and not list(asset_path.rglob("raw_extracted.md")):
            issues.append({"severity":"error","message":f"Missing raw artifact for {asset_path.name}."})
    return issues
