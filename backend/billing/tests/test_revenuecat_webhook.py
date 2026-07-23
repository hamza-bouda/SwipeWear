"""Tests for billing/revenuecat_webhook.py (KAN-73)."""
from __future__ import annotations

from uuid import uuid4

import pytest

from billing.revenuecat_webhook import WebhookParseError, parse_event, verify_signature
from billing.subscription_store import SubscriptionStatus


def _event(event_type: str, user_id=None, period_type="NORMAL", expiration_at_ms=None):
    uid = str(user_id or uuid4())
    payload: dict = {
        "api_version": "1.0",
        "event": {
            "type": event_type,
            "app_user_id": uid,
            "original_app_user_id": uid,
            "period_type": period_type,
        },
    }
    if expiration_at_ms is not None:
        payload["event"]["expiration_at_ms"] = expiration_at_ms
    return payload


class TestVerifySignature:
    def test_no_secret_configured_passes(self, monkeypatch):
        monkeypatch.setattr("billing.revenuecat_webhook._REVENUECAT_WEBHOOK_SECRET", "")
        verify_signature("anything")  # should not raise

    def test_valid_secret_passes(self, monkeypatch):
        monkeypatch.setattr("billing.revenuecat_webhook._REVENUECAT_WEBHOOK_SECRET", "mySecret")
        verify_signature("Bearer mySecret")

    def test_invalid_secret_raises(self, monkeypatch):
        monkeypatch.setattr("billing.revenuecat_webhook._REVENUECAT_WEBHOOK_SECRET", "mySecret")
        with pytest.raises(WebhookParseError):
            verify_signature("Bearer wrongSecret")

    def test_missing_header_raises(self, monkeypatch):
        monkeypatch.setattr("billing.revenuecat_webhook._REVENUECAT_WEBHOOK_SECRET", "mySecret")
        with pytest.raises(WebhookParseError):
            verify_signature(None)


class TestParseEvent:
    def test_initial_purchase_normal_is_active(self):
        uid = uuid4()
        result = parse_event(_event("INITIAL_PURCHASE", uid, "NORMAL"))
        assert result is not None
        user_id, status, rc_id, expires_at = result
        assert user_id == uid
        assert status == SubscriptionStatus.active

    def test_initial_purchase_trial_is_trialing(self):
        uid = uuid4()
        result = parse_event(_event("INITIAL_PURCHASE", uid, "TRIAL"))
        assert result is not None
        _, status, _, _ = result
        assert status == SubscriptionStatus.trialing

    def test_trial_started_is_trialing(self):
        uid = uuid4()
        result = parse_event(_event("TRIAL_STARTED", uid))
        assert result is not None
        _, status, _, _ = result
        assert status == SubscriptionStatus.trialing

    def test_renewal_is_active(self):
        uid = uuid4()
        result = parse_event(_event("RENEWAL", uid))
        _, status, _, _ = result
        assert status == SubscriptionStatus.active

    def test_cancellation_is_cancelled(self):
        uid = uuid4()
        result = parse_event(_event("CANCELLATION", uid))
        _, status, _, _ = result
        assert status == SubscriptionStatus.cancelled

    def test_expiration_is_expired(self):
        uid = uuid4()
        result = parse_event(_event("EXPIRATION", uid))
        _, status, _, _ = result
        assert status == SubscriptionStatus.expired

    def test_refund_is_refunded(self):
        uid = uuid4()
        result = parse_event(_event("REFUND", uid))
        _, status, _, _ = result
        assert status == SubscriptionStatus.refunded

    def test_subscriber_alias_returns_none(self):
        assert parse_event(_event("SUBSCRIBER_ALIAS")) is None

    def test_unknown_event_type_returns_none(self):
        assert parse_event(_event("SOMETHING_NEW")) is None

    def test_expiration_at_ms_parsed(self):
        uid = uuid4()
        exp_ms = 1_800_000_000_000  # far future
        result = parse_event(_event("RENEWAL", uid, expiration_at_ms=exp_ms))
        _, _, _, expires_at = result
        assert expires_at is not None
        assert expires_at.year > 2026

    def test_invalid_user_id_raises(self):
        payload = {"event": {"type": "RENEWAL", "app_user_id": "not-a-uuid"}}
        with pytest.raises(WebhookParseError, match="UUID"):
            parse_event(payload)

    def test_missing_user_id_raises(self):
        payload = {"event": {"type": "RENEWAL"}}
        with pytest.raises(WebhookParseError, match="app_user_id"):
            parse_event(payload)
