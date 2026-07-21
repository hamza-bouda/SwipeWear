"""Tests for preferences.store -- ProfileStore (KAN-31)."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import UUID

import pytest

from contracts.profile import (
    EditablePreferences,
    HardConstraints,
    StyleVectors,
    UserPreferenceProfile,
)
from preferences.store import ProfileConflictError, ProfileStore

USER_ID = UUID("00000000-0000-0000-0000-000000000042")
T0 = datetime(2026, 7, 20, 10, 0, 0, tzinfo=timezone.utc)


def _profile(**overrides) -> UserPreferenceProfile:
    defaults = dict(
        user_id=USER_ID,
        event_count=3,
        hard_constraints=HardConstraints(sizes=["M"], max_price_eur=50.0),
        editable_preferences=EditablePreferences(liked_brands=["Nike"]),
        vectors=StyleVectors(positive=[0.1] * 512),
        last_updated=T0,
    )
    defaults.update(overrides)
    return UserPreferenceProfile(**defaults)


def _mock_conn(fetchone_return=None, rowcount: int = 1) -> MagicMock:
    cursor = MagicMock()
    cursor.fetchone.return_value = fetchone_return
    cursor.rowcount = rowcount
    cursor.__enter__ = lambda s: s
    cursor.__exit__ = MagicMock(return_value=False)
    conn = MagicMock()
    conn.cursor.return_value = cursor
    return conn


def _row_for(profile: UserPreferenceProfile) -> tuple:
    return (
        profile.schema_version,
        profile.event_count,
        profile.hard_constraints.model_dump(),
        profile.editable_preferences.model_dump(),
        profile.vectors.model_dump(),
        profile.last_updated,
    )


class TestLoadMissingProfile:
    def test_returns_blank_valid_profile(self) -> None:
        conn = _mock_conn(fetchone_return=None)
        store = ProfileStore(lambda: conn)
        profile = store.load(USER_ID)
        assert profile.user_id == USER_ID
        assert profile.is_cold_start is True

    def test_does_not_insert_on_load(self) -> None:
        conn = _mock_conn(fetchone_return=None)
        store = ProfileStore(lambda: conn)
        store.load(USER_ID)
        cursor = conn.cursor.return_value
        assert cursor.execute.call_count == 1
        sql, _ = cursor.execute.call_args[0]
        assert sql.startswith("SELECT")


class TestLoadExistingProfile:
    def test_round_trip_fields(self) -> None:
        original = _profile()
        conn = _mock_conn(fetchone_return=_row_for(original))
        store = ProfileStore(lambda: conn)
        loaded = store.load(USER_ID)
        assert loaded == original


class TestSaveThenLoadRoundTrip:
    """AC: a save followed by a load returns exactly the same profile."""

    def test_exact_round_trip(self) -> None:
        original = _profile()
        save_conn = _mock_conn(fetchone_return=None)
        store = ProfileStore(lambda: save_conn)
        store.save(original)

        # Simulate the row now present as of the INSERT/UPSERT above.
        load_conn = _mock_conn(fetchone_return=_row_for(original))
        store_for_load = ProfileStore(lambda: load_conn)
        reloaded = store_for_load.load(USER_ID)

        assert reloaded == original


class TestSaveUnconditionalUpsert:
    def test_uses_upsert_sql_without_expected_last_updated(self) -> None:
        conn = _mock_conn()
        store = ProfileStore(lambda: conn)
        store.save(_profile())
        sql, params = conn.cursor.return_value.execute.call_args[0]
        assert "ON CONFLICT" in sql
        assert params["event_count"] == 3

    def test_commits(self) -> None:
        conn = _mock_conn()
        store = ProfileStore(lambda: conn)
        store.save(_profile())
        conn.commit.assert_called_once()


class TestSaveOptimisticLocking:
    def test_conditional_update_included_expected_timestamp(self) -> None:
        conn = _mock_conn(rowcount=1)
        store = ProfileStore(lambda: conn)
        store.save(_profile(), expected_last_updated=T0)
        sql, params = conn.cursor.return_value.execute.call_args[0]
        assert "WHERE user_id" in sql
        assert params["expected_last_updated"] == T0

    def test_raises_on_concurrent_modification(self) -> None:
        conn = _mock_conn(rowcount=0)
        store = ProfileStore(lambda: conn)
        with pytest.raises(ProfileConflictError):
            store.save(_profile(), expected_last_updated=T0)

    def test_no_conflict_when_rowcount_positive(self) -> None:
        conn = _mock_conn(rowcount=1)
        store = ProfileStore(lambda: conn)
        store.save(_profile(), expected_last_updated=T0)  # no raise
