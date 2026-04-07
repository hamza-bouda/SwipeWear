"""CRUD for user_subscriptions table (KAN-73).

Subscription state is owned by RevenueCat and synced via webhook; this module
only reads and writes the local mirror. Never call RevenueCat API directly.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID


class SubscriptionStatus(str, Enum):
    active = "active"
    trialing = "trialing"
    cancelled = "cancelled"
    expired = "expired"
    refunded = "refunded"


_UPSERT_SQL = """
INSERT INTO user_subscriptions
    (user_id, revenuecat_customer_id, status, expires_at, updated_at)
VALUES
    (%(user_id)s, %(rc_id)s, %(status)s, %(expires_at)s, now())
ON CONFLICT (user_id) DO UPDATE SET
    revenuecat_customer_id = EXCLUDED.revenuecat_customer_id,
    status                 = EXCLUDED.status,
    expires_at             = EXCLUDED.expires_at,
    updated_at             = now();
"""


def upsert_subscription(
    conn: Any,
    user_id: UUID,
    status: SubscriptionStatus,
    revenuecat_customer_id: str | None = None,
    expires_at: datetime | None = None,
) -> None:
    with conn.cursor() as cur:
        cur.execute(_UPSERT_SQL, {
            "user_id": str(user_id),
            "rc_id": revenuecat_customer_id,
            "status": status.value,
            "expires_at": expires_at,
        })
    conn.commit()


def get_subscription(
    conn: Any,
    user_id: UUID,
) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT user_id, revenuecat_customer_id, status, expires_at, updated_at "
            "FROM user_subscriptions WHERE user_id = %s",
            (str(user_id),),
        )
        row = cur.fetchone()
    if row is None:
        return None
    return {
        "user_id": row[0],
        "revenuecat_customer_id": row[1],
        "status": row[2],
        "expires_at": row[3],
        "updated_at": row[4],
    }


def is_user_premium(conn: Any, user_id: UUID) -> bool:
    """Return True if the user has an active, trialing, or not-yet-expired subscription."""
    sub = get_subscription(conn, user_id)
    if sub is None:
        return False
    status = sub["status"]
    expires_at = sub["expires_at"]
    if status in ("expired", "refunded"):
        return False
    if expires_at is not None:
        now = datetime.now(timezone.utc)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= now:
            return False
    return status in ("active", "trialing", "cancelled")
