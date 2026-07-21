"""Profile store -- Postgres persistence for UserPreferenceProfile (KAN-31).

The profile is loaded and saved whole (blueprint SS11: no hidden reads --
the ranker always receives a complete profile). Concurrent writers are
guarded by an optimistic lock on `last_updated`: pass the value returned by
a prior `load()` as `expected_last_updated` to `save()` to reject a write
that lost the race instead of silently overwriting it.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Callable
from uuid import UUID

from contracts.profile import UserPreferenceProfile

_LOG = logging.getLogger("swipewear.preferences.store")

_SELECT_SQL = """\
SELECT schema_version, event_count, hard_constraints,
       editable_preferences, vectors, updated_at
FROM user_profiles
WHERE user_id = %(user_id)s"""

_UPSERT_SQL = """\
INSERT INTO user_profiles
    (user_id, schema_version, event_count, hard_constraints,
     editable_preferences, vectors, updated_at)
VALUES
    (%(user_id)s, %(schema_version)s, %(event_count)s,
     %(hard_constraints)s::jsonb, %(editable_preferences)s::jsonb,
     %(vectors)s::jsonb, %(updated_at)s)
ON CONFLICT (user_id) DO UPDATE SET
    schema_version = EXCLUDED.schema_version,
    event_count = EXCLUDED.event_count,
    hard_constraints = EXCLUDED.hard_constraints,
    editable_preferences = EXCLUDED.editable_preferences,
    vectors = EXCLUDED.vectors,
    updated_at = EXCLUDED.updated_at"""

_CONDITIONAL_UPDATE_SQL = """\
UPDATE user_profiles
SET schema_version = %(schema_version)s,
    event_count = %(event_count)s,
    hard_constraints = %(hard_constraints)s::jsonb,
    editable_preferences = %(editable_preferences)s::jsonb,
    vectors = %(vectors)s::jsonb,
    updated_at = %(updated_at)s
WHERE user_id = %(user_id)s
  AND updated_at = %(expected_last_updated)s"""


class ProfileConflictError(Exception):
    """save() target row was modified concurrently (updated_at no longer matches)."""


def _as_dict(value: Any) -> dict:
    return json.loads(value) if isinstance(value, str) else value


def _row_params(profile: UserPreferenceProfile) -> dict[str, Any]:
    return {
        "user_id": str(profile.user_id),
        "schema_version": profile.schema_version,
        "event_count": profile.event_count,
        "hard_constraints": json.dumps(profile.hard_constraints.model_dump()),
        "editable_preferences": json.dumps(
            profile.editable_preferences.model_dump(),
        ),
        "vectors": json.dumps(profile.vectors.model_dump()),
        "updated_at": profile.last_updated,
    }


class ProfileStore:
    """Loads and saves a complete UserPreferenceProfile against Postgres.

    The connection is injected as a zero-arg factory (same shape as
    retrieval.VectorRetriever) so this module carries no hard driver
    dependency.
    """

    def __init__(self, get_conn: Callable[[], Any]) -> None:
        self._get_conn = get_conn

    def load(self, user_id: UUID) -> UserPreferenceProfile:
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(_SELECT_SQL, {"user_id": str(user_id)})
            row = cur.fetchone()

        if row is None:
            return UserPreferenceProfile(user_id=user_id)

        (
            schema_version,
            event_count,
            hard_constraints,
            editable_preferences,
            vectors,
            updated_at,
        ) = row
        return UserPreferenceProfile(
            user_id=user_id,
            schema_version=schema_version,
            event_count=event_count,
            hard_constraints=_as_dict(hard_constraints),
            editable_preferences=_as_dict(editable_preferences),
            vectors=_as_dict(vectors),
            last_updated=updated_at,
        )

    def save(
        self,
        profile: UserPreferenceProfile,
        *,
        expected_last_updated: datetime | None = None,
    ) -> None:
        """Persist `profile`.

        Pass `expected_last_updated` (the `last_updated` a prior `load()`
        returned) to enable optimistic locking -- the write is rejected
        with `ProfileConflictError` if another writer touched the row
        since. Omit it for an unconditional upsert (first save of a new
        profile, or callers that intentionally want last-writer-wins).
        """
        conn = self._get_conn()
        params = _row_params(profile)

        with conn.cursor() as cur:
            if expected_last_updated is None:
                cur.execute(_UPSERT_SQL, params)
            else:
                cur.execute(
                    _CONDITIONAL_UPDATE_SQL,
                    {**params, "expected_last_updated": expected_last_updated},
                )
                if cur.rowcount == 0:
                    raise ProfileConflictError(
                        f"user_profiles row for {profile.user_id} changed"
                        " concurrently (expected last_updated="
                        f"{expected_last_updated!r})"
                    )
        conn.commit()

        _LOG.debug(
            "Saved profile for user %s (event_count=%d, locked=%s)",
            profile.user_id,
            profile.event_count,
            expected_last_updated is not None,
        )
