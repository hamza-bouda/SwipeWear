"""KAN-74: tests for dispatch_alert_matches() in alert_runner."""
from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest

from ingestion.alert_runner import AlertMatch, dispatch_alert_matches
from vision.instance_matcher import MatchResult, MatchTier


def _make_match(tier: MatchTier = MatchTier.exact) -> AlertMatch:
    result = MatchResult(
        tier=tier,
        dinov2_score=0.90,
        fashion_score=None,
    )
    return AlertMatch(
        alert_id=UUID("aaaaaaaa-0000-0000-0000-000000000001"),
        user_id=UUID("bbbbbbbb-0000-0000-0000-000000000001"),
        result=result,
    )


class TestDispatchAlertMatches:
    def test_premium_user_no_delay(self):
        match = _make_match(MatchTier.exact)
        conn = MagicMock()

        with (
            patch(
                "ingestion.alert_runner.is_user_premium", return_value=True
            ) as mock_premium,
            patch(
                "ingestion.alert_runner.enqueue_match_notification", return_value="q-1"
            ) as mock_enqueue,
        ):
            result = dispatch_alert_matches(conn, "prod-1", [match], product_price=49.9)

        assert result == 1
        mock_premium.assert_called_once_with(conn, match.user_id)
        mock_enqueue.assert_called_once()
        call_kwargs = mock_enqueue.call_args[1]
        assert call_kwargs["is_premium"] is True
        assert call_kwargs["product_id"] == "prod-1"
        assert call_kwargs["match_tier"] == "exact"

    def test_free_tier_user(self):
        match = _make_match(MatchTier.similar)
        conn = MagicMock()

        with (
            patch("ingestion.alert_runner.is_user_premium", return_value=False),
            patch(
                "ingestion.alert_runner.enqueue_match_notification", return_value="q-2"
            ) as mock_enqueue,
        ):
            result = dispatch_alert_matches(conn, "prod-2", [match])

        assert result == 1
        call_kwargs = mock_enqueue.call_args[1]
        assert call_kwargs["is_premium"] is False

    def test_suppressed_pref_not_counted(self):
        match = _make_match()
        conn = MagicMock()

        with (
            patch("ingestion.alert_runner.is_user_premium", return_value=False),
            patch("ingestion.alert_runner.enqueue_match_notification", return_value=None),
        ):
            result = dispatch_alert_matches(conn, "prod-3", [match])

        assert result == 0

    def test_empty_matches_returns_zero(self):
        conn = MagicMock()
        with patch("ingestion.alert_runner.enqueue_match_notification") as mock_enqueue:
            result = dispatch_alert_matches(conn, "prod-4", [])
        assert result == 0
        mock_enqueue.assert_not_called()

    def test_multiple_matches_correct_count(self):
        matches = [_make_match() for _ in range(3)]
        conn = MagicMock()

        with (
            patch("ingestion.alert_runner.is_user_premium", return_value=True),
            patch(
                "ingestion.alert_runner.enqueue_match_notification",
                side_effect=["q1", None, "q3"],
            ),
        ):
            result = dispatch_alert_matches(conn, "prod-5", matches)

        assert result == 2  # one was suppressed (returned None)
