"""Parse RevenueCat webhook events and map to SubscriptionStatus (KAN-73).

RevenueCat sends a POST to /webhooks/revenuecat with Authorization: Bearer <secret>.
The app_user_id in the event payload is our user UUID (set by the mobile SDK at login).

Reference: https://www.revenuecat.com/docs/integrations/webhooks/event-types-and-fields
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from billing.subscription_store import SubscriptionStatus

_REVENUECAT_WEBHOOK_SECRET = os.environ.get("REVENUECAT_WEBHOOK_SECRET", "")

# RevenueCat event type → SubscriptionStatus mapping
_EVENT_STATUS_MAP: dict[str, SubscriptionStatus] = {
    "INITIAL_PURCHASE": SubscriptionStatus.active,
    "TRIAL_STARTED": SubscriptionStatus.trialing,
    "TRIAL_CONVERTED": SubscriptionStatus.active,
    "TRIAL_CANCELLED": SubscriptionStatus.trialing,  # still trialing until expires_at
    "RENEWAL": SubscriptionStatus.active,
    "PRODUCT_CHANGE": SubscriptionStatus.active,
    "CANCELLATION": SubscriptionStatus.cancelled,  # active until expires_at
    "EXPIRATION": SubscriptionStatus.expired,
    "REFUND": SubscriptionStatus.refunded,
    "SUBSCRIBER_ALIAS": None,  # not a status change
}


class WebhookParseError(Exception):
    pass


def verify_signature(authorization_header: str | None) -> None:
    """Raise WebhookParseError if the Authorization header doesn't match the shared secret."""
    if not _REVENUECAT_WEBHOOK_SECRET:
        return  # secret not configured — skip in dev
    expected = f"Bearer {_REVENUECAT_WEBHOOK_SECRET}"
    if authorization_header != expected:
        raise WebhookParseError("Invalid Authorization header")


def parse_event(
    payload: dict[str, Any],
) -> tuple[UUID, SubscriptionStatus, str | None, datetime | None] | None:
    """Parse a RevenueCat webhook payload.

    Returns (user_id, status, rc_customer_id, expires_at) or None if the event
    should be silently ignored (e.g. SUBSCRIBER_ALIAS).

    Raises WebhookParseError on invalid payloads.
    """
    event = payload.get("event", {})
    event_type = event.get("type", "")

    if event_type not in _EVENT_STATUS_MAP:
        return None  # unknown event type — ignore

    status = _EVENT_STATUS_MAP[event_type]
    if status is None:
        return None  # SUBSCRIBER_ALIAS or similar — ignore

    app_user_id = event.get("app_user_id") or event.get("original_app_user_id")
    if not app_user_id:
        raise WebhookParseError("Missing app_user_id in event payload")

    try:
        user_id = UUID(app_user_id)
    except ValueError:
        raise WebhookParseError(f"app_user_id is not a valid UUID: {app_user_id!r}")

    # INITIAL_PURCHASE with period_type=TRIAL → trialing, not active
    if event_type == "INITIAL_PURCHASE" and event.get("period_type") == "TRIAL":
        status = SubscriptionStatus.trialing

    rc_customer_id = event.get("original_app_user_id") or app_user_id

    expires_at: datetime | None = None
    expiration_ms = event.get("expiration_at_ms")
    if expiration_ms is not None:
        expires_at = datetime.fromtimestamp(expiration_ms / 1000, tz=timezone.utc)

    return user_id, status, rc_customer_id, expires_at
