"""Tests for preferences.rebuild -- rebuild_profile from the event log (KAN-35)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from uuid import UUID

import pytest

from contracts.events import EventType, InteractionEvent
from preferences._event_replay import replay_events_in_memory
from preferences.rebuild import rebuild_profile

USER_ID = UUID("00000000-0000-0000-0000-000000000042")
T0 = datetime(2026, 7, 20, 10, 0, 0, tzinfo=timezone.utc)


def make_event(event_type, minutes, **payload):
    return InteractionEvent(
        user_id=USER_ID,
        product_id=f"prod-{minutes:03d}",
        event_type=event_type,
        payload=payload,
        timestamp=T0 + timedelta(minutes=minutes),
    )


TEN_EVENTS = [
    make_event(EventType.swipe_right, 1, brand="Nike", product_embedding=[1.0, 0.0]),
    make_event(EventType.swipe_right, 2, brand="Carhartt", product_embedding=[0.0, 1.0]),
    make_event(EventType.swipe_left_style, 3, product_embedding=[1.0, 1.0]),
    make_event(EventType.swipe_left_price, 4, product_price_eur=200.0),
    make_event(EventType.save, 5, brand="Nike", product_embedding=[1.0, 0.0]),
    make_event(EventType.open, 6, product_embedding=[0.5, 0.5]),
    make_event(EventType.edit_preference, 7, field="liked_brands", value="Stussy"),
    make_event(EventType.edit_preference, 8, field="rejected_brands", value="Zara"),
    make_event(EventType.swipe_right, 9, brand="Carhartt", product_embedding=[0.2, 0.8]),
    make_event(EventType.swipe_left_price, 10, product_price_eur=90.0),
]


def _row_for(event: InteractionEvent) -> tuple:
    return (
        event.event_id,
        event.user_id,
        event.product_id,
        event.event_type.value,
        event.payload,
        event.timestamp,
        event.schema_version,
    )


def _mock_conn(events: list[InteractionEvent]) -> MagicMock:
    cursor = MagicMock()
    cursor.fetchall.return_value = [_row_for(e) for e in events]
    cursor.__enter__ = lambda s: s
    cursor.__exit__ = MagicMock(return_value=False)
    conn = MagicMock()
    conn.cursor.return_value = cursor
    return conn


class TestRebuildMatchesEventByEventReplay:
    def test_rebuild_produces_same_profile_as_manual_replay(self) -> None:
        conn = _mock_conn(TEN_EVENTS)
        rebuilt = rebuild_profile(USER_ID, get_conn=lambda: conn)
        expected = replay_events_in_memory(TEN_EVENTS, user_id=USER_ID)
        assert rebuilt == expected

    def test_rebuild_event_count_matches_number_of_events(self) -> None:
        conn = _mock_conn(TEN_EVENTS)
        rebuilt = rebuild_profile(USER_ID, get_conn=lambda: conn)
        assert rebuilt.event_count == 10


class TestRebuildIsIdempotent:
    def test_rebuilding_twice_gives_identical_profile(self) -> None:
        conn = _mock_conn(TEN_EVENTS)
        first = rebuild_profile(USER_ID, get_conn=lambda: conn)
        second = rebuild_profile(USER_ID, get_conn=lambda: conn)
        assert first == second


class TestRebuildEmptyHistory:
    def test_no_events_returns_cold_start_profile(self) -> None:
        conn = _mock_conn([])
        rebuilt = rebuild_profile(USER_ID, get_conn=lambda: conn)
        assert rebuilt.is_cold_start is True


class TestRebuildUntilBound:
    def test_until_is_passed_through_to_the_query(self) -> None:
        conn = _mock_conn(TEN_EVENTS[:4])
        cutoff = T0 + timedelta(minutes=4)
        rebuild_profile(USER_ID, cutoff, get_conn=lambda: conn)

        cursor = conn.cursor.return_value
        _sql, params = cursor.execute.call_args[0]
        assert params["until"] == cutoff
        assert "timestamp <=" in _sql

    def test_no_until_omits_the_bound_from_the_query(self) -> None:
        conn = _mock_conn(TEN_EVENTS)
        rebuild_profile(USER_ID, get_conn=lambda: conn)

        cursor = conn.cursor.return_value
        sql, params = cursor.execute.call_args[0]
        assert "until" not in params
        assert "timestamp <=" not in sql


class TestRebuildQueriesByUserId:
    def test_user_id_passed_as_string(self) -> None:
        conn = _mock_conn(TEN_EVENTS)
        rebuild_profile(USER_ID, get_conn=lambda: conn)

        cursor = conn.cursor.return_value
        _sql, params = cursor.execute.call_args[0]
        assert params["user_id"] == str(USER_ID)
