"""DB CRUD for device tokens and notification flushing (KAN-71)."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from notifications.push_sender import PushMessage, send_batch

_LOG = logging.getLogger("swipewear.notifications.store")

_MATCH_TIER_LABELS = {
    "exact": "La même pièce est disponible",
    "similar": "Une pièce très proche est disponible",
}


def register_device_token(
    conn: Any,
    user_id: UUID,
    expo_token: str,
    platform: str = "unknown",
) -> None:
    """Upsert an Expo device token for a user."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO device_tokens (user_id, expo_token, platform, last_seen_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (user_id, expo_token) DO UPDATE
                SET last_seen_at = EXCLUDED.last_seen_at,
                    platform = EXCLUDED.platform
            """,
            (str(user_id), expo_token, platform),
        )
    conn.commit()


def get_device_tokens(conn: Any, user_id: UUID) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT expo_token FROM device_tokens WHERE user_id = %s",
            (str(user_id),),
        )
        return [row[0] for row in cur.fetchall()]


def mark_notification_opened(conn: Any, queue_id: str) -> None:
    """Record that a user opened a push notification (for tracking)."""
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE notification_log SET opened_at = NOW() WHERE queue_id = %s",
            (queue_id,),
        )
    conn.commit()


def flush_due_notifications(conn: Any) -> int:
    """Process all pending queue entries whose scheduled_for <= now.

    Fetches due entries, sends push via Expo, marks sent_at and logs.
    Returns the number of messages sent.
    """
    now = datetime.now(timezone.utc)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT q.queue_id, q.user_id, q.alert_id, q.product_id,
                   q.match_tier, q.product_price, q.product_image, q.is_digest
            FROM notification_queue q
            WHERE q.sent_at IS NULL AND q.scheduled_for <= %s
            ORDER BY q.scheduled_for
            LIMIT 500
            """,
            (now,),
        )
        rows = cur.fetchall()

    if not rows:
        return 0

    total_sent = 0
    for row in rows:
        queue_id, user_id, alert_id, product_id, match_tier, product_price, product_image, is_digest = row
        tokens = get_device_tokens(conn, UUID(str(user_id)))
        if not tokens:
            _mark_sent(conn, str(queue_id))
            continue

        title, body = _build_message_text(match_tier, product_price, is_digest)
        messages = [
            PushMessage(
                to=token,
                title=title,
                body=body,
                data={
                    "product_id": product_id,
                    "alert_id": str(alert_id),
                    "queue_id": str(queue_id),
                    "tier": match_tier,
                },
            )
            for token in tokens
        ]

        receipts = send_batch(messages)
        _mark_sent(conn, str(queue_id))
        _log_receipts(conn, str(queue_id), str(user_id), receipts)
        total_sent += len([r for r in receipts if r.status == "ok"])

    return total_sent


def _mark_sent(conn: Any, queue_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE notification_queue SET sent_at = NOW() WHERE queue_id = %s",
            (queue_id,),
        )
    conn.commit()


def _log_receipts(conn: Any, queue_id: str, user_id: str, receipts) -> None:
    with conn.cursor() as cur:
        for r in receipts:
            cur.execute(
                """
                INSERT INTO notification_log (queue_id, user_id, expo_token, expo_status)
                VALUES (%s, %s, %s, %s)
                """,
                (queue_id, user_id, r.token, r.status),
            )
    conn.commit()


def _build_message_text(match_tier: str, product_price: float | None, is_digest: bool) -> tuple[str, str]:
    label = _MATCH_TIER_LABELS.get(match_tier, "Une alerte a matché")
    if is_digest:
        title = "Vos alertes SwipeWear"
        body = "Plusieurs nouvelles pièces correspondent à vos alertes — jetez un œil !"
    else:
        title = "SwipeWear — Nouvelle alerte"
        price_str = f" · {product_price:.0f} €" if product_price is not None else ""
        body = f"{label}{price_str}"
    return title, body
