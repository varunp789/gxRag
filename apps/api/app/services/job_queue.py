"""Durable queue facade used by the API and the worker.

Redis is the production transport.  A JSON spool is deliberately retained as a
local-development fallback so a lost Redis connection never turns a requested
reprocess into a silently discarded job.
"""

from __future__ import annotations

import json
from pathlib import Path
from threading import Lock

import redis

from app.core.config import settings


_lock = Lock()


def _spool_path() -> Path:
    return Path(settings.processing_state_path).with_suffix(".queue.json")

def _dead_letter_path() -> Path:
    return Path(settings.processing_state_path).with_suffix(".dead-letter.json")


def _read_spool() -> list[str]:
    path = _spool_path()
    if not path.exists():
        return []
    return json.loads(path.read_text())


def _write_spool(items: list[str]) -> None:
    path = _spool_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items))


def _redis_client() -> redis.Redis | None:
    try:
        client = redis.from_url(settings.redis_url, decode_responses=True)
        client.ping()
        return client
    except redis.RedisError:
        return None


def enqueue(job_id: str) -> str:
    """Queue a job exactly once at the transport boundary where possible."""
    client = _redis_client()
    if client is not None:
        client.rpush(settings.processing_queue, job_id)
        return "redis"
    with _lock:
        items = _read_spool()
        if job_id not in items:
            items.append(job_id)
            _write_spool(items)
    return "local_spool"


def dequeue(timeout_seconds: int = 5) -> str | None:
    client = _redis_client()
    if client is not None:
        result = client.blpop(settings.processing_queue, timeout=timeout_seconds)
        return result[1] if result else None
    with _lock:
        items = _read_spool()
        if not items:
            return None
        job_id = items.pop(0)
        _write_spool(items)
        return job_id

def dead_letter(job_id: str, reason: str) -> None:
    path=_dead_letter_path(); path.parent.mkdir(parents=True, exist_ok=True)
    items=json.loads(path.read_text()) if path.exists() else []
    items.append({"job_id":job_id,"reason":reason})
    path.write_text(json.dumps(items, indent=2))

def backlog() -> dict[str, int]:
    client=_redis_client()
    if client is not None: return {"ready": client.llen(settings.processing_queue), "dead_letter": client.llen(f"{settings.processing_queue}:dead")}
    return {"ready":len(_read_spool()), "dead_letter":len(json.loads(_dead_letter_path().read_text())) if _dead_letter_path().exists() else 0}
