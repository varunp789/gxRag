"""Workspace API keys: hashed at rest, shown once, revocable."""

from __future__ import annotations

import hmac
from uuid import uuid4

from app.core.security import generate_api_key, hash_api_key_secret, split_api_key
from app.db import store as db_store
from app.models.access import ApiKey
from app.services import catalog

# In-memory fallback (no database): (ApiKey, secret_hash | None). Seeded catalog
# keys carry no secret and therefore cannot authenticate.
_KEYS: dict[str, tuple[ApiKey, str | None]] = {}


def _ensure_seed() -> None:
    if not _KEYS:
        for key in catalog.API_KEYS:
            _KEYS[key.id] = (key, None)


def reset() -> None:
    _KEYS.clear()


def create_key(workspace_id: str, name: str, role: str) -> tuple[ApiKey, str]:
    full_key, prefix, secret_hash = generate_api_key()
    key = ApiKey(id=f"key_{uuid4().hex[:10]}", workspace_id=workspace_id, name=name,
                 prefix=prefix, role=role, status="active")
    if db_store.enabled():
        with db_store.connection() as conn, conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO api_keys (id, workspace_id, name, prefix, key_hash, role, status) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (key.id, workspace_id, name, prefix, secret_hash, role, "active"),
            )
            conn.commit()
    else:
        _ensure_seed()
        _KEYS[key.id] = (key, secret_hash)
    return key, full_key


def list_keys(workspace_id: str) -> list[ApiKey]:
    if db_store.enabled():
        with db_store.connection() as conn, conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, workspace_id, name, prefix, role, status FROM api_keys "
                "WHERE workspace_id = %s ORDER BY created_at", (workspace_id,))
            return [ApiKey(id=a, workspace_id=b, name=c, prefix=d, role=e, status=f)
                    for a, b, c, d, e, f in cursor.fetchall()]
    _ensure_seed()
    return [key for key, _ in _KEYS.values() if key.workspace_id == workspace_id]


def revoke_key(workspace_id: str, key_id: str) -> bool:
    if db_store.enabled():
        with db_store.connection() as conn, conn.cursor() as cursor:
            cursor.execute(
                "UPDATE api_keys SET status = 'revoked', revoked_at = now() "
                "WHERE id = %s AND workspace_id = %s AND status = 'active'", (key_id, workspace_id))
            changed = cursor.rowcount > 0
            conn.commit()
            return changed
    _ensure_seed()
    entry = _KEYS.get(key_id)
    if entry is None or entry[0].workspace_id != workspace_id or entry[0].status != "active":
        return False
    _KEYS[key_id] = (entry[0].model_copy(update={"status": "revoked"}), entry[1])
    return True


def authenticate_key(value: str) -> ApiKey | None:
    """Return the active key matching ``value`` or None. Constant-time compare."""
    parsed = split_api_key(value)
    if parsed is None:
        return None
    prefix, secret = parsed
    candidate = hash_api_key_secret(secret)
    if db_store.enabled():
        with db_store.connection() as conn, conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, workspace_id, name, prefix, role, status, key_hash FROM api_keys "
                "WHERE prefix = %s", (prefix,))
            row = cursor.fetchone()
        if row is None or row[6] is None or row[5] != "active":
            return None
        stored, key = row[6], ApiKey(id=row[0], workspace_id=row[1], name=row[2],
                                     prefix=row[3], role=row[4], status=row[5])
    else:
        _ensure_seed()
        match = next(((k, h) for k, h in _KEYS.values() if k.prefix == prefix), None)
        if match is None or match[1] is None or match[0].status != "active":
            return None
        key, stored = match
    return key if hmac.compare_digest(stored, candidate) else None
