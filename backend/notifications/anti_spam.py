"""Anti-spam rules for push notifications (KAN-71).

Rules (all MANDATORY per ticket spec):
1. Max 3 individual notifications per user per calendar day (UTC).
   Matches beyond cap → digest flag set, sent as daily summary.
2. Quiet hours: no notifications between 22:00 and 08:00 UTC.
   (Per-device timezone recalibration is post-MVP.)
   Outside-hours sends → rescheduled to 08:00 next morning UTC.
3. Batching: multiple matches of the same alert within 1 hour → one notification.
   The latest match replaces the pending queued entry.
4. Per-alert frequency preference: instant / daily_digest / disabled.

The 30-minute delay for free-tier accounts (E13-02 preparation) is applied
by the caller (dispatcher.py) before passing scheduled_for here.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

_LOG = logging.getLogger("swipewear.notifications.anti_spam")

_DAILY_LIMIT = 3
_QUIET_START_HOUR = 22
_QUIET_END_HOUR = 8
_BATCH_WINDOW_SECONDS = 3600


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def count_sent_today(conn: Any, user_id: UUID) -> int:
    """Count individual (non-digest) notifications sent today (UTC)."""
    today = _now_utc().date()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) FROM notification_queue
            WHERE user_id = %s
              AND is_digest = FALSE
              AND sent_at IS NOT NULL
              AND sent_at::date = %s
            """,
            (str(user_id), today),
        )
        return cur.fetchone()[0]


def get_preference(conn: Any, user_id: UUID, alert_id: UUID) -> str:
    """Return frequency preference: 'instant' | 'daily_digest' | 'disabled'."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT frequency FROM alert_notification_prefs WHERE user_id = %s AND alert_id = %s",
            (str(user_id), str(alert_id)),
        )
        row = cur.fetchone()
    return row[0] if row else "instant"


def find_pending_within_window(conn: Any, user_id: UUID, alert_id: UUID) -> str | None:
    """Return queue_id of a pending (unsent) notification for this alert within 1h."""
    cutoff = _now_utc() - timedelta(seconds=_BATCH_WINDOW_SECONDS)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT queue_id FROM notification_queue
            WHERE user_id = %s AND alert_id = %s
              AND sent_at IS NULL
              AND created_at >= %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (str(user_id), str(alert_id), cutoff),
        )
        row = cur.fetchone()
    return str(row[0]) if row else None


def apply_quiet_hours(scheduled_for: datetime) -> datetime:
    """Shift a scheduled send time past quiet hours if needed."""
    hour = scheduled_for.hour
    if _QUIET_START_HOUR <= hour or hour < _QUIET_END_HOUR:
        next_morning = scheduled_for.replace(
            hour=_QUIET_END_HOUR, minute=0, second=0, microsecond=0,
        )
        if hour >= _QUIET_START_HOUR:
            next_morning += timedelta(days=1)
        return next_morning
    return scheduled_for


def should_send_as_digest(conn: Any, user_id: UUID) -> bool:
    """True if user already hit the daily individual notification limit."""
    return count_sent_today(conn, user_id) >= _DAILY_LIMIT
