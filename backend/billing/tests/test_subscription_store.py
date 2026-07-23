"""Tests for billing/subscription_store.py (KAN-73)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from billing.subscription_store import SubscriptionStatus, is_user_premium, upsert_subscription


def _mock_conn(row=None):
    cursor = MagicMock()
    cursor.fetchone.return_value = row
    cursor.__enter__ = lambda s: s
    cursor.__exit__ = MagicMock(return_value=False)
    conn = MagicMock()
    conn.cursor.return_value = cursor
    return conn


class TestIsPremium:
    def _sub(self, status: str, expires_at=None):
        return {
            "user_id": uuid4(),
            "revenuecat_customer_id": "rc_123",
            "status": status,
            "expires_at": expires_at,
            "updated_at": datetime.now(timezone.utc),
        }

    def test_active_no_expiry_is_premium(self):
        from unittest.mock import patch
        uid = uuid4()
        conn = _mock_conn()
        with patch("billing.subscription_store.get_subscription", return_value=self._sub("active")):
            assert is_user_premium(conn, uid)

    def test_trialing_is_premium(self):
        from unittest.mock import patch
        uid = uuid4()
        conn = _mock_conn()
        with patch("billing.subscription_store.get_subscription", return_value=self._sub("trialing")):
            assert is_user_premium(conn, uid)

    def test_cancelled_not_yet_expired_is_premium(self):
        from unittest.mock import patch
        uid = uuid4()
        conn = _mock_conn()
        future = datetime.now(timezone.utc) + timedelta(days=3)
        with patch("billing.subscription_store.get_subscription", return_value=self._sub("cancelled", future)):
            assert is_user_premium(conn, uid)

    def test_cancelled_and_expired_is_not_premium(self):
        from unittest.mock import patch
        uid = uuid4()
        conn = _mock_conn()
        past = datetime.now(timezone.utc) - timedelta(days=1)
        with patch("billing.subscription_store.get_subscription", return_value=self._sub("cancelled", past)):
            assert not is_user_premium(conn, uid)

    def test_expired_status_is_not_premium(self):
        from unittest.mock import patch
        uid = uuid4()
        conn = _mock_conn()
        with patch("billing.subscription_store.get_subscription", return_value=self._sub("expired")):
            assert not is_user_premium(conn, uid)

    def test_refunded_is_not_premium(self):
        from unittest.mock import patch
        uid = uuid4()
        conn = _mock_conn()
        with patch("billing.subscription_store.get_subscription", return_value=self._sub("refunded")):
            assert not is_user_premium(conn, uid)

    def test_no_subscription_is_not_premium(self):
        from unittest.mock import patch
        uid = uuid4()
        conn = _mock_conn()
        with patch("billing.subscription_store.get_subscription", return_value=None):
            assert not is_user_premium(conn, uid)
