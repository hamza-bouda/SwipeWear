"""Unit tests for contracts/alerts.py (KAN-69)."""
from __future__ import annotations

from uuid import uuid4

import pytest

from contracts.alerts import (
    FREE_ALERT_LIMIT,
    Alert,
    AlertConstraints,
    AlertStatus,
    AlertType,
)


class TestAlertDefaults:
    def test_specific_item_alert(self):
        a = Alert(
            user_id=uuid4(),
            alert_type=AlertType.specific_item,
            label="Air Max 90 taille 42",
            reference_product_id="ebay-123",
        )
        assert a.status == AlertStatus.active
        assert a.constraints.max_price_eur is None
        assert a.constraints.sizes == []
        assert a.schema_version == 1

    def test_style_alert_with_constraints(self):
        a = Alert(
            user_id=uuid4(),
            alert_type=AlertType.style,
            label="Veste vintage marron",
            constraints=AlertConstraints(max_price_eur=40.0, sizes=["M", "L"]),
        )
        assert a.constraints.max_price_eur == 40.0
        assert "M" in a.constraints.sizes

    def test_reference_embedding_optional(self):
        a = Alert(user_id=uuid4(), alert_type=AlertType.style, label="test")
        assert a.reference_embedding is None

    def test_free_alert_limit_constant(self):
        assert FREE_ALERT_LIMIT == 3

    def test_pause_status(self):
        a = Alert(
            user_id=uuid4(),
            alert_type=AlertType.style,
            label="test",
            status=AlertStatus.paused,
        )
        assert a.status == AlertStatus.paused

    def test_unique_ids(self):
        u = uuid4()
        a1 = Alert(user_id=u, alert_type=AlertType.style, label="a")
        a2 = Alert(user_id=u, alert_type=AlertType.style, label="b")
        assert a1.alert_id != a2.alert_id
