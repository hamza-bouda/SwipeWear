"""Rebuild a user's profile from the event log (KAN-35, blueprint SS11 rule 6).

The event log is the source of truth: if the update algorithm changes
(alpha/beta weights, new event rules -- preferences/config.py, updater.py),
every stored profile can be recomputed from scratch by replaying its events,
instead of trusting whatever is currently persisted. rebuild_profile is a
thin loader around the replay logic that already existed in
_event_replay.py (built for KAN-32) -- it only adds the Postgres read.

Deliberately does not save the rebuilt profile itself: this module answers
"what should this profile be", persistence is the caller's decision (see
scripts/rebuild_all_profiles.py for the batch job that does both).
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Callable
from uuid import UUID

from contracts.events import InteractionEvent
from contracts.profile import UserPreferenceProfile
from preferences._event_replay import replay_events_in_memory

_SELECT_EVENTS_SQL = """\
SELECT event_id, user_id, product_id, event_type, payload, timestamp, schema_version
FROM interaction_events
WHERE user_id = %(user_id)s
ORDER BY timestamp ASC"""

_SELECT_EVENTS_UNTIL_SQL = """\
SELECT event_id, user_id, product_id, event_type, payload, timestamp, schema_version
FROM interaction_events
WHERE user_id = %(user_id)s AND timestamp <= %(until)s
ORDER BY timestamp ASC"""


def _as_dict(value: Any) -> dict:
    return json.loads(value) if isinstance(value, str) else value


def _load_events(
    get_conn: Callable[[], Any],
    user_id: UUID,
    until: datetime | None,
) -> list[InteractionEvent]:
    conn = get_conn()
    params: dict[str, Any] = {"user_id": str(user_id)}
    sql = _SELECT_EVENTS_SQL
    if until is not None:
        sql = _SELECT_EVENTS_UNTIL_SQL
        params["until"] = until

    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    return [
        InteractionEvent(
            event_id=event_id,
            user_id=row_user_id,
            product_id=product_id,
            event_type=event_type,
            payload=_as_dict(payload),
            timestamp=timestamp,
            schema_version=schema_version,
        )
        for event_id, row_user_id, product_id, event_type, payload, timestamp, schema_version in rows
    ]


def rebuild_profile(
    user_id: UUID,
    until: datetime | None = None,
    *,
    get_conn: Callable[[], Any],
) -> UserPreferenceProfile:
    """Recompute `user_id`'s profile from its full event history.

    `until` optionally bounds the replay to events at or before that
    timestamp (e.g. to inspect what the profile looked like at a past
    point). Rebuilding twice with the same arguments always yields the
    same profile: replay starts from a fresh UserPreferenceProfile and
    applies the same sorted events through the same pure PreferenceUpdater
    rules each time.

    `get_conn` is injected (same shape as ProfileStore) rather than
    imported, so this module carries no hard driver dependency.
    """
    events = _load_events(get_conn, user_id, until)
    return replay_events_in_memory(events, user_id=user_id, until=until)
