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
    def test_a_created_account_can_be_found_again(self, user_id):
        store.create_user(user_id, "Alice@Example.com", "hunter2")
        found = store.get_user_by_email("alice@example.com")
        assert found is not None
        assert found.user_id == user_id

    def test_email_lookup_is_case_insensitive(self, user_id):
        store.create_user(user_id, "Bob@Example.com", "hunter2")
        assert store.get_user_by_email("BOB@EXAMPLE.COM") is not None

    def test_the_password_is_never_stored_in_clear(self, user_id):
        store.create_user(user_id, "carol@example.com", "hunter2")
        record = store.get_user(user_id)
        assert "hunter2" not in record.password_hash
        assert store.verify_password("hunter2", record.password_hash)
        assert not store.verify_password("wrong", record.password_hash)

    def test_unknown_email_returns_none(self):
        assert store.get_user_by_email("nobody@example.com") is None


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
        store.create_user(user_id, "dave@example.com", "hunter2")
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


class TestPasswordHashing:
    """Passwords were a single unsalted-per-user SHA-256 round: fast to guess
    from a stolen dump, and two accounts sharing a password shared a hash."""

    def test_the_same_password_yields_different_hashes(self):
        first = store._hash_password("hunter2")
        second = store._hash_password("hunter2")
        assert first != second, "a per-account salt must make hashes unique"
        assert store.verify_password("hunter2", first)
        assert store.verify_password("hunter2", second)

    def test_wrong_password_is_rejected(self):
        stored = store._hash_password("hunter2")
        assert not store.verify_password("hunter3", stored)

    def test_hash_records_its_parameters(self):
        """Cost can be raised later without invalidating existing passwords."""
        stored = store._hash_password("hunter2")
        algorithm, n, r, p, salt, digest = stored.split("$")
        assert algorithm == "scrypt"
        assert (int(n), int(r), int(p)) == (
            store._SCRYPT_N, store._SCRYPT_R, store._SCRYPT_P,
        )
        assert len(bytes.fromhex(salt)) == 16
        assert len(bytes.fromhex(digest)) == store._SCRYPT_DKLEN

    def test_legacy_sha256_hashes_still_authenticate(self):
        """An account created before the change must not be locked out."""
        import hashlib
        legacy = hashlib.sha256(
            f"{store._pepper()}:hunter2".encode()
        ).hexdigest()
        assert store.verify_password("hunter2", legacy)
        assert not store.verify_password("wrong", legacy)

    def test_a_malformed_stored_hash_is_a_failed_login_not_a_crash(self):
        for broken in ("scrypt$", "scrypt$a$b$c$d$e", "scrypt$1$2$3$zz$zz"):
            assert store.verify_password("hunter2", broken) is False

    def test_needs_rehash_flags_legacy_and_outdated_parameters(self):
        assert store.needs_rehash("deadbeef" * 8) is True
        assert store.needs_rehash("scrypt$1024$8$1$aa$bb") is True
        assert store.needs_rehash(store._hash_password("hunter2")) is False
