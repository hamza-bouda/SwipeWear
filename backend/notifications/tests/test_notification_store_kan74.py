"""KAN-74: tests for the missed-deals logic in flush_due_notifications."""
from __future__ import annotations

from unittest.mock import MagicMock, call, patch

import pytest

from notifications.notification_store import (
    _is_product_available,
    _record_missed_deal,
    count_missed_deals,
    flush_due_notifications,
)


def _make_conn(rows=None, fetchone_val=None):
    """Build a minimal psycopg2-like mock connection."""
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value.__enter__ = lambda s: cur
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    cur.fetchall.return_value = rows or []
    cur.fetchone.return_value = fetchone_val
    return conn, cur


class TestIsProductAvailable:
    def test_available_true(self):
        conn, cur = _make_conn(fetchone_val=(True,))
        assert _is_product_available(conn, "prod-1") is True

    def test_available_false(self):
        conn, cur = _make_conn(fetchone_val=(False,))
        assert _is_product_available(conn, "prod-1") is False

    def test_product_not_found_returns_false(self):
        conn, cur = _make_conn(fetchone_val=None)
        assert _is_product_available(conn, "prod-missing") is False


class TestRecordMissedDeal:
    def test_inserts_row(self):
        conn, cur = _make_conn()
        _record_missed_deal(conn, "user-1", "alert-1", "prod-1")
        cur.execute.assert_called_once()
        call_args = cur.execute.call_args[0]
        assert "INSERT INTO missed_deals" in call_args[0]
        assert ("user-1", "alert-1", "prod-1") == call_args[1]
        conn.commit.assert_called_once()


class TestCountMissedDeals:
    def test_returns_count(self):
        from uuid import UUID
        conn, cur = _make_conn(fetchone_val=(7,))
        result = count_missed_deals(conn, UUID("00000000-0000-0000-0000-000000000001"))
        assert result == 7


class TestFlushDueNotificationsMissedDeal:
    """flush_due_notifications() should record missed deal and skip send when product unavailable."""

    def _queue_row(self):
        from uuid import uuid4
        return (
            str(uuid4()),   # queue_id
            str(uuid4()),   # user_id
            str(uuid4()),   # alert_id
            "prod-sold",    # product_id
            "exact",        # match_tier
            49.99,          # product_price
            None,           # product_image
            False,          # is_digest
        )

    def test_sold_out_product_records_missed_deal_and_skips_send(self):
        row = self._queue_row()
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value.__enter__ = lambda s: cur
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        cur.fetchall.return_value = [row]

        with (
            patch("notifications.notification_store._is_product_available", return_value=False) as mock_avail,
            patch("notifications.notification_store._record_missed_deal") as mock_missed,
            patch("notifications.notification_store._mark_sent") as mock_mark,
            patch("notifications.notification_store.send_batch") as mock_send,
        ):
            result = flush_due_notifications(conn)

        assert result == 0  # no notification sent
        mock_avail.assert_called_once_with(conn, "prod-sold")
        mock_missed.assert_called_once()
        mock_mark.assert_called_once_with(conn, row[0])
        mock_send.assert_not_called()

    def test_available_product_proceeds_to_send(self):
        row = self._queue_row()
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value.__enter__ = lambda s: cur
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        cur.fetchall.return_value = [row]

        from notifications.push_sender import PushReceipt
        mock_receipt = PushReceipt(token="ExponentPushToken[x]", status="ok", message=None)

        with (
            patch("notifications.notification_store._is_product_available", return_value=True),
            patch("notifications.notification_store._record_missed_deal") as mock_missed,
            patch("notifications.notification_store.get_device_tokens", return_value=["ExponentPushToken[x]"]),
            patch("notifications.notification_store.send_batch", return_value=[mock_receipt]),
            patch("notifications.notification_store._mark_sent"),
            patch("notifications.notification_store._log_receipts"),
        ):
            result = flush_due_notifications(conn)

        assert result == 1
        mock_missed.assert_not_called()
