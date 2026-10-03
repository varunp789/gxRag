"""Stripe customer mapping and webhook event de-duplication."""

from __future__ import annotations

from app.db import store as db_store
from app.services import catalog

_CUSTOMERS: dict[str, str] = {}
_SEEN_EVENTS: set[tuple[str, str]] = set()


def reset() -> None:
    _CUSTOMERS.clear()
    _SEEN_EVENTS.clear()


def customer_for_tenant(tenant_id: str) -> str | None:
    if db_store.enabled():
        with db_store.connection() as conn, conn.cursor() as cursor:
            cursor.execute("SELECT stripe_customer_id FROM tenants WHERE id = %s", (tenant_id,))
            row = cursor.fetchone()
            return row[0] if row else None
    return _CUSTOMERS.get(tenant_id)


def link_customer(tenant_id: str, customer_id: str) -> bool:
    """Map a tenant to its Stripe customer. False if the tenant is unknown or the customer is taken."""
    if catalog.get_tenant(tenant_id) is None:
        return False
    if db_store.enabled():
        import psycopg
        try:
            with db_store.connection() as conn, conn.cursor() as cursor:
                cursor.execute("UPDATE tenants SET stripe_customer_id = %s WHERE id = %s", (customer_id, tenant_id))
                conn.commit()
        except psycopg.errors.UniqueViolation:
            return False
        return True
    if customer_id in {value for key, value in _CUSTOMERS.items() if key != tenant_id}:
        return False
    _CUSTOMERS[tenant_id] = customer_id
    return True


def tenant_for_customer(customer_id: str) -> str | None:
    if db_store.enabled():
        with db_store.connection() as conn, conn.cursor() as cursor:
            cursor.execute("SELECT id FROM tenants WHERE stripe_customer_id = %s", (customer_id,))
            row = cursor.fetchone()
            return row[0] if row else None
    return next((tenant for tenant, customer in _CUSTOMERS.items() if customer == customer_id), None)


def first_delivery(provider: str, event_id: str) -> bool:
    """Record an event id; False means it was already processed (replay)."""
    if db_store.enabled():
        with db_store.connection() as conn, conn.cursor() as cursor:
            cursor.execute("INSERT INTO webhook_events (provider, event_id) VALUES (%s,%s) ON CONFLICT DO NOTHING",
                           (provider, event_id))
            inserted = cursor.rowcount == 1
            conn.commit()
            return inserted
    key = (provider, event_id)
    if key in _SEEN_EVENTS:
        return False
    _SEEN_EVENTS.add(key)
    return True
