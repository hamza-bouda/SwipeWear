"""Billing endpoints — RevenueCat webhook + user premium status (KAN-73).

POST /webhooks/revenuecat   — RevenueCat sends subscription events here
GET  /billing/status        — current user's subscription status
"""
from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from api.auth import get_current_user_id
from api.db import get_conn, put_conn
from billing.revenuecat_webhook import WebhookParseError, parse_event, verify_signature
from billing.subscription_store import get_subscription, is_user_premium, upsert_subscription

_LOG = logging.getLogger("swipewear.api.billing")

router = APIRouter(tags=["billing"])


@router.post("/webhooks/revenuecat", status_code=200)
async def revenuecat_webhook(
    request: Request,
    authorization: str | None = Header(default=None),
):
    try:
        verify_signature(authorization)
    except WebhookParseError as exc:
        raise HTTPException(status_code=401, detail=str(exc))

    payload = await request.json()

    try:
        result = parse_event(payload)
    except WebhookParseError as exc:
        _LOG.warning("Ignoring malformed RevenueCat event: %s", exc)
        return {"status": "ignored", "reason": str(exc)}

    if result is None:
        return {"status": "ignored"}

    user_id, status, rc_customer_id, expires_at = result

    conn = get_conn()
    try:
        upsert_subscription(conn, user_id, status, rc_customer_id, expires_at)
        _LOG.info(
            "RevenueCat event processed: user=%s status=%s expires_at=%s",
            user_id, status, expires_at,
        )
    except Exception:
        _LOG.exception("Failed to upsert subscription for user %s", user_id)
        raise HTTPException(status_code=500, detail="Failed to store subscription")
    finally:
        put_conn(conn)

    return {"status": "ok"}


@router.get("/billing/status")
def billing_status(user_id: UUID = Depends(get_current_user_id)):
    conn = get_conn()
    try:
        sub = get_subscription(conn, user_id)
        premium = is_user_premium(conn, user_id)
    finally:
        put_conn(conn)

    if sub is None:
        return {
            "is_premium": False,
            "status": None,
            "expires_at": None,
        }

    return {
        "is_premium": premium,
        "status": sub["status"],
        "expires_at": sub["expires_at"].isoformat() if sub["expires_at"] else None,
    }
