"""Tests for the PostgreSQL-backed account store — KAN-88.

Accounts, profiles and the event log used to live in module-level dicts. Every
restart erased every customer, and a second replica served a different memory
from the first. These tests assert the data outlives the objects that wrote it.
"""
from __future__ import annotations

import os
from unittest.mock import patch
from uuid import uuid4

import pytest

from api import store
from contracts.events import EventType, InteractionEvent
from contracts.profile import UserPreferenceProfile

pytestmark = pytest.mark.requires_db


@pytest.fixture()
def product_id():
    from api.db import get_conn, put_conn

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM products LIMIT 1")
            row = cur.fetchone()
    finally:
        put_conn(conn)
    if row is None:
        pytest.skip("catalogue is empty — run scripts/ingest_catalogue.py")
    return row[0]


@pytest.fixture()
def user_id():
    uid = uuid4()
    yield uid
    store.delete_user(uid)


class TestAccounts:
    """Accounts are provisioned from a verified Supabase token (KAN-90).

    There is no local password any more, so nothing here hashes or checks one.
    """

    def test_a_provisioned_account_can_be_found_again(self, user_id):
        store.upsert_external_user(user_id, "Alice@Example.com", "google")
        found = store.get_user(user_id)
        assert found is not None
        assert found.user_id == user_id

    def test_the_email_is_normalised(self, user_id):
        store.upsert_external_user(user_id, "Bob@Example.COM", "email")
        assert store.get_user(user_id).email == "bob@example.com"

    def test_no_password_is_ever_stored(self, user_id):
        store.upsert_external_user(user_id, "carol@example.com", "apple")
        assert store.get_user(user_id).password_hash is None

    def test_a_second_sync_updates_rather_than_duplicates(self, user_id):
        """The provider is the source of truth for the address.

        A user who changes their email upstream would otherwise keep the stale
        one here forever.
        """
        store.upsert_external_user(user_id, "old@example.com", "email")
        store.upsert_external_user(user_id, "new@example.com", "email")
        assert store.get_user(user_id).email == "new@example.com"

    def test_a_provider_may_withhold_the_address(self, user_id):
        """Sign in with Apple can hide it; the row must still exist."""
        store.upsert_external_user(user_id, None, "apple")
        assert store.get_user(user_id) is not None
        assert store.get_user(user_id).email is None

    def test_unknown_user_returns_none(self):
        assert store.get_user(uuid4()) is None


class TestSurvivesRestart:
    def test_profile_outlives_the_process_that_wrote_it(self, user_id):
        """The whole point: a dict cannot do this."""
        profile = UserPreferenceProfile(user_id=user_id)
        profile.editable_preferences.liked_brands.append("Nike")
        store.save_profile(profile)

        # Nothing in-process is reused — this is what a redeploy looks like.
        reloaded = store.get_or_create_profile(user_id)
        assert reloaded.editable_preferences.liked_brands == ["Nike"]

    def test_unknown_user_gets_an_empty_profile_not_an_error(self):
        profile = store.get_or_create_profile(uuid4())
        assert profile.event_count == 0
        assert profile.is_cold_start


class TestEventLog:
    def test_events_round_trip(self, user_id, product_id):
        event = InteractionEvent(
            user_id=user_id,
            product_id=product_id,
            event_type=EventType.swipe_right,
            payload={"brand": "Nike"},
        )
        store.append_event(event)

        events = store.get_events_for_user(user_id)
        assert [e.event_id for e in events] == [event.event_id]
        assert events[0].payload["brand"] == "Nike"

    def test_preference_edits_are_logged_without_a_product(self, user_id):
        """A preference edit concerns no product; product_id is nullable so it
        does not need a fake row to point at."""
        store.append_event(InteractionEvent(
            user_id=user_id,
            product_id="profile",
            event_type=EventType.edit_preference,
            payload={"action": "add", "field": "liked_brands", "value": "Nike"},
        ))
        events = store.get_events_for_user(user_id)
        assert len(events) == 1
        assert events[0].event_type == EventType.edit_preference

    def test_events_are_scoped_to_their_user(self, user_id, product_id):
        other = uuid4()
        try:
            store.append_event(InteractionEvent(
                user_id=other, product_id=product_id,
                event_type=EventType.swipe_right, payload={},
            ))
            assert store.get_events_for_user(user_id) == []
        finally:
            store.delete_user(other)


class TestErasure:
    def test_delete_removes_the_account_its_profile_and_its_events(
        self, user_id, product_id,
    ):
        store.upsert_external_user(user_id, "dave@example.com", "google")
        store.save_profile(UserPreferenceProfile(user_id=user_id))
        store.append_event(InteractionEvent(
            user_id=user_id, product_id=product_id,
            event_type=EventType.swipe_right, payload={},
        ))

        assert store.delete_user(user_id) is True
        assert store.get_user(user_id) is None
        assert store.get_events_for_user(user_id) == []
        assert store.get_or_create_profile(user_id).event_count == 0

    def test_deleting_an_unknown_account_reports_false(self):
        assert store.delete_user(uuid4()) is False


class TestAnonymousMigration:
    def test_profile_and_events_follow_the_new_identity(self, product_id):
        anonymous, registered = uuid4(), uuid4()
        try:
            profile = UserPreferenceProfile(user_id=anonymous)
            profile.editable_preferences.liked_brands.append("Carhartt")
            store.save_profile(profile)
            store.append_event(InteractionEvent(
                user_id=anonymous, product_id=product_id,
                event_type=EventType.swipe_right, payload={},
            ))

            assert store.migrate_anonymous_profile(anonymous, registered) is True
            assert store.get_or_create_profile(
                registered
            ).editable_preferences.liked_brands == ["Carhartt"]
            assert len(store.get_events_for_user(registered)) == 1
            # Moved, not copied — the same profile must not answer to both ids.
            assert store.get_events_for_user(anonymous) == []
        finally:
            store.delete_user(anonymous)
            store.delete_user(registered)

    def test_nothing_to_migrate_reports_false(self):
        assert store.migrate_anonymous_profile(uuid4(), uuid4()) is False


class TestResetGuard:
    def test_reset_refuses_to_run_in_production(self):
        """It used to clear four dicts; it now empties three tables."""
        with patch.dict(os.environ, {"APP_ENV": "production"}):
            with pytest.raises(RuntimeError, match="refusing to run in"):
                store.reset()
