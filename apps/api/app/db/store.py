"""PostgreSQL-backed persistence for the asset registry, usage and audit log.

The registry keeps hot state in module-level lists (API and worker both import
them).  When ``GXRAG_DATABASE_URL`` is set this module is the system of record:

* ``load_all`` is called on entry to every registry operation so API and worker
  processes always observe each other's writes.
* ``save_all`` upserts only rows whose content changed since they were loaded,
  which keeps a stale process from overwriting a newer row it never touched.
"""

from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

import psycopg
from psycopg.types.json import Jsonb

from app.core.config import settings

# state key -> (table, scoping columns derived from the model dict)
TABLES: dict[str, tuple[str, tuple[str, ...]]] = {
    "assets": ("assets", ("workspace_id", "tenant_id", "status")),
    "sources": ("asset_sources", ("asset_id",)),
    "uploads": ("asset_uploads", ("asset_id",)),
    "versions": ("asset_versions", ("asset_id",)),
    "jobs": ("processing_jobs", ("asset_id", "workspace_id", "status")),
    "artifacts": ("artifacts", ("asset_id", "workspace_id", "artifact_type")),
    "indexes": ("index_records", ("asset_id", "workspace_id", "index_type", "status")),
}
# Parents must be written before children because of foreign keys.
WRITE_ORDER = ["assets", "sources", "uploads", "versions", "jobs", "artifacts", "indexes"]

_loaded_hashes: dict[tuple[str, str], str] = {}


def enabled() -> bool:
    return bool(settings.database_url)


@contextmanager
def connection() -> Iterator[psycopg.Connection]:
    if not settings.database_url:
        raise RuntimeError("GXRAG_DATABASE_URL is not configured.")
    with psycopg.connect(settings.database_url, connect_timeout=5) as conn:
        yield conn


def _digest(row: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(row, sort_keys=True, default=str).encode()).hexdigest()


def load_all() -> dict[str, list[dict[str, Any]]]:
    payload: dict[str, list[dict[str, Any]]] = {}
    with connection() as conn, conn.cursor() as cursor:
        for key in WRITE_ORDER:
            table = TABLES[key][0]
            cursor.execute(f"SELECT data FROM {table} ORDER BY id")  # noqa: S608 - fixed table names
            payload[key] = [row[0] for row in cursor.fetchall()]
    _loaded_hashes.clear()
    for key, rows in payload.items():
        for row in rows:
            _loaded_hashes[(key, row["id"])] = _digest(row)
    return payload


def save_all(payload: dict[str, list[dict[str, Any]]]) -> int:
    """Upsert rows changed since they were loaded. Returns the number written."""
    written = 0
    with connection() as conn, conn.cursor() as cursor:
        for key in WRITE_ORDER:
            table, scope_columns = TABLES[key]
            for row in payload.get(key, []):
                digest = _digest(row)
                if _loaded_hashes.get((key, row["id"])) == digest:
                    continue
                columns = ["id", *scope_columns, "data"]
                values = [row["id"], *[row.get(column) for column in scope_columns], Jsonb(row)]
                assignments = ", ".join(f"{column} = EXCLUDED.{column}" for column in columns[1:])
                if table in {"assets", "processing_jobs"}:
                    assignments += ", updated_at = now()"
                cursor.execute(
                    f"INSERT INTO {table} ({', '.join(columns)}) "  # noqa: S608 - fixed table names
                    f"VALUES ({', '.join(['%s'] * len(columns))}) "
                    f"ON CONFLICT (id) DO UPDATE SET {assignments}",
                    values,
                )
                _loaded_hashes[(key, row["id"])] = digest
                written += 1
        conn.commit()
    return written


def current_period(now: datetime | None = None) -> str:
    return (now or datetime.now(timezone.utc)).strftime("%Y-%m")


def increment_usage(workspace_id: str, unit: str, count: int) -> None:
    with connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO usage_counters (workspace_id, period, unit, quantity) VALUES (%s,%s,%s,%s) "
            "ON CONFLICT (workspace_id, period, unit) DO UPDATE "
            "SET quantity = usage_counters.quantity + EXCLUDED.quantity",
            (workspace_id, current_period(), unit, count),
        )
        conn.commit()


def read_usage(workspace_id: str) -> dict[str, int]:
    with connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            "SELECT unit, quantity FROM usage_counters WHERE workspace_id = %s AND period = %s",
            (workspace_id, current_period()),
        )
        return {unit: int(quantity) for unit, quantity in cursor.fetchall()}


def insert_audit(actor: str, action: str, resource_type: str, resource_id: str, workspace_id: str | None) -> None:
    with connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO audit_logs (actor, action, resource_type, resource_id, workspace_id) "
            "VALUES (%s,%s,%s,%s,%s)",
            (actor, action, resource_type, resource_id, workspace_id),
        )
        conn.commit()


def read_audit(workspace_id: str | None, limit: int) -> list[dict[str, str]]:
    query = ("SELECT actor, action, resource_type, resource_id, workspace_id, occurred_at "
             "FROM audit_logs ")
    params: list[Any] = []
    if workspace_id is not None:
        query += "WHERE workspace_id = %s "
        params.append(workspace_id)
    query += "ORDER BY id DESC LIMIT %s"
    params.append(limit)
    with connection() as conn, conn.cursor() as cursor:
        cursor.execute(query, params)
        return [
            {"actor": a, "action": b, "resource_type": c, "resource_id": d,
             "workspace_id": e or "", "occurred_at": f.isoformat()}
            for a, b, c, d, e, f in cursor.fetchall()
        ]
