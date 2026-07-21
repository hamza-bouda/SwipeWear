
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from contracts.events import EventType, InteractionEvent
from preferences._event_replay import replay_events_in_memory

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


FIVE_EVENTS = [
    make_event(EventType.swipe_right, 1),
    make_event(EventType.swipe_right, 2),
    make_event(EventType.swipe_left_price, 3, product_price_eur=200.0),
    make_event(EventType.save, 4),
    make_event(EventType.edit_preference, 5, field="liked_brands", value="Nike"),
]


class TestReplayEvents:
    def test_replay_5_events_increments_event_count(self):
        profile = replay_events_in_memory(FIVE_EVENTS, user_id=USER_ID)
        assert profile.event_count == 5

    def test_replay_sets_user_id(self):
        profile = replay_events_in_memory(FIVE_EVENTS, user_id=USER_ID)
        assert profile.user_id == USER_ID

    def test_price_constraint_set_by_swipe_left_price(self):
        # KAN-32: max_price_eur = min(current, product_price * 0.9) -- a 10%
        # margin below the price the user rejected, not the price itself.
        profile = replay_events_in_memory(FIVE_EVENTS, user_id=USER_ID)
        assert profile.hard_constraints.max_price_eur == 180.0

    def test_edit_preference_adds_liked_brand(self):
        profile = replay_events_in_memory(FIVE_EVENTS, user_id=USER_ID)
        assert "Nike" in profile.editable_preferences.liked_brands

    def test_last_updated_equals_last_event_timestamp(self):
        profile = replay_events_in_memory(FIVE_EVENTS, user_id=USER_ID)
        assert profile.last_updated == T0 + timedelta(minutes=5)

    def test_until_filter_stops_replay_early(self):
        cutoff = T0 + timedelta(minutes=3)
        profile = replay_events_in_memory(FIVE_EVENTS, user_id=USER_ID, until=cutoff)
        assert profile.event_count == 3
        assert profile.editable_preferences.liked_brands == []

    def test_empty_event_list_returns_blank_profile(self):
        profile = replay_events_in_memory([], user_id=USER_ID)
        assert profile.event_count == 0
        assert profile.is_cold_start is True

    def test_events_replayed_in_chronological_order(self):
        events = [
            make_event(EventType.swipe_left_price, 10, product_price_eur=200.0),
            make_event(EventType.edit_preference, 5, field="max_price_eur", value=80.0),
        ]
        profile = replay_events_in_memory(events, user_id=USER_ID)
        # edit at minute 5 runs first => max=80; swipe at minute 10 => 200 > 80, not updated
        assert profile.hard_constraints.max_price_eur == 80.0
