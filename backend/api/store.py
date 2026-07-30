"""User accounts, profiles and the event log, backed by PostgreSQL.

This module used to hold everything in process memory with the note "will be
replaced by PostgreSQL". It never was, which meant accounts existed only until
the next restart, a second replica could not see the first one's users, and
POST /events wrote the profile to user_profiles while GET /profile read the
dict — so a swipe and the profile screen disagreed by construction.

The function signatures are unchanged so the routers keep working; only where
the data lives has moved.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from uuid import UUID

from api.config import is_production
from api.db import get_conn, put_conn
from contracts.events import EventType, InteractionEvent
from contracts.profile import UserPreferenceProfile
from preferences.interfaces import ProfileStore


@dataclass
class UserRecord:
    user_id: UUID
    # Both are optional since KAN-90: an externally authenticated account has
    # no password here at all, and a provider may withhold the address.
    email: str | None
    password_hash: str | None
    # Raw Firebase uid. user_id is its UUIDv5 derivation, which only computes
    # one way, so deleting the account upstream needs the original (KAN-91).
    provider_uid: str | None = None
    # Phone sign-in creates accounts with no email at all.
    phone_number: str | None = None


class _Connection:
    """Borrow a pooled connection and always hand it back."""

    def __enter__(self):
        self._conn = get_conn()
        return self._conn

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is not None:
            # A failed statement leaves psycopg2 in InFailedSqlTransaction, so
            # the next borrower of this pooled connection would fail too.
            try:
                self._conn.rollback()
            except Exception:  # noqa: BLE001 - never mask the original error
                pass
        put_conn(self._conn)
        return False


# ── Profiles ─────────────────────────────────────────────────────────────────

def get_or_create_profile(user_id: UUID) -> UserPreferenceProfile:
    """Return the stored profile, or an empty one for a first-time user."""
    with _Connection() as conn:
        # ProfileStore.load already returns a blank profile when the row is
        # absent, so there is nothing to create here — the row appears on the
        # first save, which is what keeps a browsing visitor out of the table.
        return ProfileStore(lambda: conn).load(user_id)


def save_profile(profile: UserPreferenceProfile) -> None:
    with _Connection() as conn:
        ProfileStore(lambda: conn).save(profile)
        conn.commit()


# ── Event log ────────────────────────────────────────────────────────────────

_INSERT_EVENT_SQL = """\
INSERT INTO interaction_events
    (event_id, user_id, product_id, event_type, payload, timestamp,
     schema_version)
VALUES (%(event_id)s, %(user_id)s, %(product_id)s, %(event_type)s,
        %(payload)s::jsonb, %(timestamp)s, %(schema_version)s)
ON CONFLICT (event_id) DO NOTHING"""

_SELECT_EVENTS_SQL = """\
SELECT event_id, user_id, product_id, event_type, payload, timestamp,
       schema_version
FROM interaction_events
WHERE user_id = %(user_id)s
ORDER BY timestamp"""

# profile.py records preference edits, which concern no product. The column is
# nullable (migration 014) rather than carrying a sentinel that the foreign key
# onto products would reject.
_NO_PRODUCT = "profile"


def append_event(event: InteractionEvent) -> None:
    product_id = event.product_id
    if not product_id or product_id == _NO_PRODUCT:
        product_id = None
    with _Connection() as conn:
        with conn.cursor() as cur:
            cur.execute(_INSERT_EVENT_SQL, {
                "event_id": str(event.event_id),
                "user_id": str(event.user_id),
                "product_id": product_id,
                "event_type": event.event_type.value,
                "payload": json.dumps(event.payload),
                "timestamp": event.timestamp,
                "schema_version": event.schema_version,
            })
        conn.commit()


def get_events_for_user(user_id: UUID) -> list[InteractionEvent]:
    with _Connection() as conn:
        with conn.cursor() as cur:
            cur.execute(_SELECT_EVENTS_SQL, {"user_id": str(user_id)})
            rows = cur.fetchall()

    events: list[InteractionEvent] = []
    for event_id, uid, product_id, event_type, payload, timestamp, version in rows:
        events.append(InteractionEvent(
            event_id=event_id,
            user_id=uid,
            product_id=product_id or _NO_PRODUCT,
            event_type=EventType(event_type),
            payload=payload if isinstance(payload, dict) else json.loads(payload),
            timestamp=timestamp,
            schema_version=version,
        ))
    return events


# ── Accounts ─────────────────────────────────────────────────────────────────

def upsert_external_user(
    user_id: UUID,
    email: str | None,
    provider: str,
    provider_uid: str | None = None,
    phone_number: str | None = None,
) -> UserRecord:
    """Record an account authenticated by Firebase, creating it on first sight.

    Provisioning happens here rather than at a signup endpoint because there is
    no signup endpoint any more: the first time a valid token arrives, that
    person exists. Contact details are refreshed on every call — someone who
    changes their address upstream would otherwise keep the stale one forever.

    `provider_uid` is the raw Firebase uid. It is kept because deleting the
    account upstream needs it, and `user_id` is a one-way UUIDv5 derivation of
    it (see api/firebase_auth.local_user_id).
    """
    normalised = email.lower() if email else None
    with _Connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users"
                " (user_id, email, auth_provider, provider_uid, phone_number)"
                " VALUES (%s, %s, %s, %s, %s)"
                " ON CONFLICT (user_id) DO UPDATE"
                "   SET email = EXCLUDED.email,"
                "       auth_provider = EXCLUDED.auth_provider,"
                "       provider_uid = COALESCE("
                "           EXCLUDED.provider_uid, users.provider_uid),"
                "       phone_number = EXCLUDED.phone_number",
                (str(user_id), normalised, provider, provider_uid, phone_number),
            )
        conn.commit()
    return UserRecord(
        user_id=user_id, email=normalised, password_hash=None,
        provider_uid=provider_uid, phone_number=phone_number,
    )


def _row_to_user(row) -> UserRecord:
    # UserRecord declares a UUID; the driver may hand back the column as text
    # depending on how the connection was set up, and a str/UUID mismatch
    # compares unequal without ever raising.
    user_id = row[0] if isinstance(row[0], UUID) else UUID(str(row[0]))
    return UserRecord(
        user_id=user_id, email=row[1], password_hash=row[2],
        provider_uid=row[3], phone_number=row[4],
    )


def get_user(user_id: UUID) -> UserRecord | None:
    with _Connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id, email, password_hash, provider_uid, phone_number"
                " FROM users WHERE user_id = %s",
                (str(user_id),),
            )
            row = cur.fetchone()
    return _row_to_user(row) if row else None


def delete_user(user_id: UUID) -> bool:
    """Erase the account and everything attached to it (GDPR right to erasure)."""
    with _Connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE user_id = %s", (str(user_id),))
            deleted = cur.rowcount > 0
            # Not ON DELETE CASCADE: profiles and events are keyed by user_id
            # without a foreign key onto users, because a user can browse and
            # accumulate a profile before ever creating an account.
            cur.execute(
                "DELETE FROM interaction_events WHERE user_id = %s",
                (str(user_id),),
            )
            cur.execute(
                "DELETE FROM user_profiles WHERE user_id = %s", (str(user_id),),
            )
        conn.commit()
    return deleted


def migrate_anonymous_profile(anonymous_id: UUID, new_id: UUID) -> bool:
    """Carry an anonymous visitor's profile and events onto their new account."""
    with _Connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM user_profiles WHERE user_id = %s",
                (str(anonymous_id),),
            )
            if cur.fetchone() is None:
                return False
            # Move rather than copy: leaving the anonymous row behind would
            # let the same profile be served under two identities.
            cur.execute(
                "DELETE FROM user_profiles WHERE user_id = %s", (str(new_id),),
            )
            cur.execute(
                "UPDATE user_profiles SET user_id = %s WHERE user_id = %s",
                (str(new_id), str(anonymous_id)),
            )
            cur.execute(
                "UPDATE interaction_events SET user_id = %s WHERE user_id = %s",
                (str(new_id), str(anonymous_id)),
            )
        conn.commit()
    return True


def reset() -> None:
    """Clear all accounts, profiles and events. Tests only.

    Guarded rather than trusted: this used to empty four dicts, and now it
    empties three tables. Called against a production database it would delete
    every customer.
    """
    if is_production():
        raise RuntimeError(
            "store.reset() would delete every account — refusing to run in "
            "production."
        )
    with _Connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM interaction_events")
            cur.execute("DELETE FROM user_profiles")
            cur.execute("DELETE FROM users")
        conn.commit()
