"""Tests for anti-spam rules (KAN-71)."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from notifications.anti_spam import (
    _DAILY_LIMIT,
    _QUIET_END_HOUR,
    _QUIET_START_HOUR,
    apply_quiet_hours,
    should_send_as_digest,
)


class TestQuietHours:
    def _dt(self, hour: int) -> datetime:
        return datetime(2026, 7, 23, hour, 0, 0, tzinfo=timezone.utc)

    def test_sends_at_noon(self):
        assert apply_quiet_hours(self._dt(12)) == self._dt(12)

    def test_shifts_22h_to_next_morning(self):
        result = apply_quiet_hours(self._dt(22))
        assert result.hour == _QUIET_END_HOUR
        assert result.day == 24

    def test_shifts_23h_to_next_morning(self):
        result = apply_quiet_hours(self._dt(23))
        assert result.hour == _QUIET_END_HOUR

    def test_shifts_2h_to_same_morning(self):
        result = apply_quiet_hours(self._dt(2))
        assert result.hour == _QUIET_END_HOUR
        assert result.day == 23

    def test_boundary_8h_allowed(self):
        assert apply_quiet_hours(self._dt(8)) == self._dt(8)

    def test_boundary_21h_allowed(self):
        assert apply_quiet_hours(self._dt(21)) == self._dt(21)


class TestDailyLimit:
    def _mock_conn(self, count: int) -> MagicMock:
        conn = MagicMock()
        ctx = conn.cursor.return_value.__enter__.return_value
        ctx.fetchone.return_value = (count,)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        return conn

    def test_below_limit_not_digest(self):
        conn = self._mock_conn(_DAILY_LIMIT - 1)
        assert not should_send_as_digest(conn, MagicMock())

    def test_at_limit_is_digest(self):
        conn = self._mock_conn(_DAILY_LIMIT)
        assert should_send_as_digest(conn, MagicMock())

    def test_above_limit_is_digest(self):
        conn = self._mock_conn(_DAILY_LIMIT + 5)
        assert should_send_as_digest(conn, MagicMock())


class TestDispatcherEnqueue:
    def test_disabled_preference_suppresses(self):
        from notifications.dispatcher import enqueue_match_notification
        from uuid import uuid4
        conn = MagicMock()
        with patch("notifications.dispatcher.get_preference", return_value="disabled"):
            result = enqueue_match_notification(
                conn, uuid4(), uuid4(), "p1", "exact"
            )
        assert result is None

    def test_enqueues_with_free_tier_delay(self):
        from notifications.dispatcher import _FREE_TIER_DELAY_SECONDS, enqueue_match_notification
        from uuid import uuid4
        conn = MagicMock()
        inserted_rows = {}

        def fake_insert(conn, user_id, alert_id, product_id, match_tier,
                        product_price, product_image, is_digest, scheduled_for):
            inserted_rows["scheduled_for"] = scheduled_for
            return "fake-queue-id"

        with patch("notifications.dispatcher.get_preference", return_value="instant"), \
             patch("notifications.dispatcher.should_send_as_digest", return_value=False), \
             patch("notifications.dispatcher.find_pending_within_window", return_value=None), \
             patch("notifications.dispatcher._insert_queue_entry", side_effect=fake_insert):
            enqueue_match_notification(conn, uuid4(), uuid4(), "p1", "exact", is_premium=False)

        now = __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        )
        delay = (inserted_rows["scheduled_for"] - now).total_seconds()
        assert delay >= _FREE_TIER_DELAY_SECONDS - 5

    def test_premium_no_delay(self):
        from notifications.dispatcher import _FREE_TIER_DELAY_SECONDS, enqueue_match_notification
        from uuid import uuid4
        conn = MagicMock()
        inserted_rows = {}

        def fake_insert(conn, user_id, alert_id, product_id, match_tier,
                        product_price, product_image, is_digest, scheduled_for):
            inserted_rows["scheduled_for"] = scheduled_for
            return "fake-queue-id"

        with patch("notifications.dispatcher.get_preference", return_value="instant"), \
             patch("notifications.dispatcher.should_send_as_digest", return_value=False), \
             patch("notifications.dispatcher.find_pending_within_window", return_value=None), \
             patch("notifications.dispatcher._insert_queue_entry", side_effect=fake_insert):
            enqueue_match_notification(conn, uuid4(), uuid4(), "p1", "exact", is_premium=True)

        now = __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        )
        delay = (inserted_rows["scheduled_for"] - now).total_seconds()
        assert delay < _FREE_TIER_DELAY_SECONDS


class TestPushSender:
    def test_empty_batch_returns_empty(self):
        from notifications.push_sender import send_batch
        assert send_batch([]) == []

    def test_message_text_exact_tier(self):
        from notifications.notification_store import _build_message_text
        title, body = _build_message_text("exact", 45.0, is_digest=False)
        assert "pièce" in body.lower()
        assert "45" in body

    def test_message_text_digest(self):
        from notifications.notification_store import _build_message_text
        title, body = _build_message_text("exact", None, is_digest=True)
        assert "alertes" in body.lower()


class TestNotificationsApiRouter:
    def test_register_invalid_token(self):
        from fastapi.testclient import TestClient
        from api.app import app
        from api.auth import create_anonymous_token
        from uuid import uuid4
        client = TestClient(app)
        token = create_anonymous_token(uuid4())
        resp = client.post(
            "/notifications/register",
            json={"expo_token": "not-a-valid-token", "platform": "ios"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400

    def test_register_valid_token_calls_store(self):
        from fastapi.testclient import TestClient
        from unittest.mock import patch
        from api.app import app
        from api.auth import create_anonymous_token
        from uuid import uuid4
        client = TestClient(app)
        user_id = uuid4()
        token = create_anonymous_token(user_id)
        with patch("api.routers.notifications.get_conn") as mock_get, \
             patch("api.routers.notifications.put_conn"), \
             patch("api.routers.notifications.register_device_token") as mock_reg:
            mock_get.return_value = MagicMock()
            resp = client.post(
                "/notifications/register",
                json={"expo_token": "ExponentPushToken[abc123]", "platform": "ios"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 201
        assert mock_reg.called
