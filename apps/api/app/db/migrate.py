"""Minimal forward-only SQL migration runner.

Usage: python -m app.db.migrate [--seed]
"""

from __future__ import annotations

import sys
from pathlib import Path

import psycopg

from app.core.config import settings

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def pending_migrations(applied: set[str]) -> list[Path]:
    return [path for path in sorted(MIGRATIONS_DIR.glob("*.sql")) if path.name not in applied]


def migrate(database_url: str | None = None) -> list[str]:
    url = database_url or settings.database_url
    if not url:
        raise RuntimeError("GXRAG_DATABASE_URL is not configured.")
    applied_now: list[str] = []
    with psycopg.connect(url, autocommit=False) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(727274)")
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations "
                "(name text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"
            )
            cursor.execute("SELECT name FROM schema_migrations")
            applied = {row[0] for row in cursor.fetchall()}
            for path in pending_migrations(applied):
                cursor.execute(path.read_text())
                cursor.execute("INSERT INTO schema_migrations (name) VALUES (%s)", (path.name,))
                applied_now.append(path.name)
        connection.commit()
    return applied_now


def seed_catalog(database_url: str | None = None) -> None:
    """Load the built-in catalog (plans, tenants, workspaces, users) idempotently."""
    from app.services import catalog

    url = database_url or settings.database_url
    if not url:
        raise RuntimeError("GXRAG_DATABASE_URL is not configured.")
    with psycopg.connect(url) as connection:
        with connection.cursor() as cursor:
            for plan in catalog.PLANS:
                cursor.execute(
                    "INSERT INTO plans VALUES (%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING",
                    (plan.id, plan.name, plan.monthly_document_limit, plan.monthly_query_limit, plan.max_workspace_members),
                )
            for tenant in catalog.TENANTS:
                cursor.execute(
                    "INSERT INTO tenants VALUES (%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING",
                    (tenant.id, tenant.name, tenant.slug, tenant.plan_id, tenant.status),
                )
            for workspace in catalog.WORKSPACES:
                cursor.execute(
                    "INSERT INTO workspaces VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING",
                    (workspace.id, workspace.tenant_id, workspace.name, workspace.slug,
                     workspace.environment, workspace.region, workspace.status),
                )
            for user in catalog.USERS:
                cursor.execute(
                    "INSERT INTO users VALUES (%s,%s,%s) ON CONFLICT (id) DO NOTHING",
                    (user.id, user.email, user.full_name),
                )
            for admin in catalog.ADMIN_USERS:
                cursor.execute(
                    "INSERT INTO admin_users VALUES (%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING",
                    (admin.id, admin.email, admin.full_name, admin.roles),
                )
            for member in catalog.WORKSPACE_MEMBERS:
                cursor.execute(
                    "INSERT INTO workspace_members VALUES (%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING",
                    (member.id, member.workspace_id, member.user_id, member.role, member.status),
                )
        connection.commit()


if __name__ == "__main__":
    for name in migrate():
        print(f"applied {name}")
    if "--seed" in sys.argv:
        seed_catalog()
        print("seeded catalog")
