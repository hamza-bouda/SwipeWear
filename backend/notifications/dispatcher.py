"""Alert match → push notification dispatcher (KAN-71).

Enqueues notifications into notification_queue, applying anti-spam rules:
- Checks per-alert preference (instant / daily_digest / disabled)
- Checks daily limit (→ digest if exceeded)
- Checks quiet hours (→ shifts scheduled_for)
- Checks 1h batching window (→ updates existing pending entry)
- Applies 30-min delay for free-tier accounts (E13-02 preparation)

A separate cron job (scripts/run_notifications_cron.py) flushes the queue
by calling notification_store.flush_due_notifications().
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from notifications.anti_spam import (
    apply_quiet_hours,
    find_pending_within_window,
    get_preference,
    should_send_as_digest,
)

_LOG = logging.getLogger("swipewear.notifications.dispatcher")

_FREE_TIER_DELAY_SECONDS = 1800


def enqueue_match_notification(
    conn: Any,
    user_id: UUID,
    alert_id: UUID,
    product_id: str,
    match_tier: str,
    product_price: float | None = None,
    product_image: str | None = None,
    is_premium: bool = False,
) -> str | None:
    """Enqueue a push notification for an alert match.

    Returns the queue_id if enqueued, None if suppressed (disabled pref).
    """
    pref = get_preference(conn, user_id, alert_id)
    if pref == "disabled":
        _LOG.debug("Notification suppressed (disabled pref) for user %s alert %s", user_id, alert_id)
        return None

    is_digest = pref == "daily_digest" or should_send_as_digest(conn, user_id)

    scheduled_for = datetime.now(timezone.utc)
    if not is_premium:
        scheduled_for += timedelta(seconds=_FREE_TIER_DELAY_SECONDS)
    scheduled_for = apply_quiet_hours(scheduled_for)

    # Batch: if there's already a pending notification for this alert within 1h,
    # update it with the latest product instead of creating a new entry.
    existing_id = find_pending_within_window(conn, user_id, alert_id)
    if existing_id and not is_digest:
        _update_queued_entry(conn, existing_id, product_id, match_tier, product_price, product_image, scheduled_for)
        _LOG.debug("Batched into existing queue_id=%s", existing_id)
        return existing_id

    queue_id = _insert_queue_entry(
        conn, user_id, alert_id, product_id, match_tier,
        product_price, product_image, is_digest, scheduled_for,
    )
    _LOG.info(
        "Enqueued notification queue_id=%s user=%s alert=%s tier=%s digest=%s scheduled=%s",
        queue_id, user_id, alert_id, match_tier, is_digest, scheduled_for.isoformat(),
    )
    return queue_id


def _insert_queue_entry(
    conn: Any,
    user_id: UUID,
    alert_id: UUID,
    product_id: str,
    match_tier: str,
    product_price: float | None,
    product_image: str | None,
    is_digest: bool,
    scheduled_for: datetime,
) -> str:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO notification_queue
                (user_id, alert_id, product_id, match_tier, product_price,
                 product_image, is_digest, scheduled_for)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING queue_id
            """,
            (
                str(user_id), str(alert_id), product_id, match_tier,
                product_price, product_image, is_digest, scheduled_for,
            ),
        )
        queue_id = str(cur.fetchone()[0])
    conn.commit()
    return queue_id


def _update_queued_entry(
    conn: Any,
    queue_id: str,
    product_id: str,
    match_tier: str,
    product_price: float | None,
    product_image: str | None,
    scheduled_for: datetime,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE notification_queue
            SET product_id = %s, match_tier = %s, product_price = %s,
                product_image = %s, scheduled_for = %s
            WHERE queue_id = %s AND sent_at IS NULL
            """,
            (product_id, match_tier, product_price, product_image, scheduled_for, queue_id),
        )
    conn.commit()
