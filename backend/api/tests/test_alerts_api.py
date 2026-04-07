"""End-to-end API tests for /alerts endpoints (KAN-69).

The DB is mocked — this tests routing, auth, and business logic (free tier cap).
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from api.app import app
from api.auth import create_token
from contracts.alerts import Alert, AlertStatus, AlertType


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def user_id():
    return uuid4()


@pytest.fixture()
def auth_headers(user_id):
    return {"Authorization": f"Bearer {create_token(user_id)}"}


def _make_alert(user_id, alert_type=AlertType.style, label="test", status=AlertStatus.active):
    return Alert(user_id=user_id, alert_type=alert_type, label=label, status=status)


def _mock_conn():
    conn = MagicMock()
    conn.cursor.return_value.__enter__ = lambda s: s
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return conn


class TestCreateAlert:
    def test_create_style_alert(self, client, user_id, auth_headers):
        with patch("api.routers.alerts.get_conn") as mock_get, \
             patch("api.routers.alerts.put_conn"), \
             patch("api.routers.alerts.count_active_alerts", return_value=0), \
             patch("api.routers.alerts.create_alert") as mock_create:
            mock_get.return_value = _mock_conn()
            mock_create.side_effect = lambda conn, alert: alert

            resp = client.post(
                "/alerts",
                json={
                    "alert_type": "style",
                    "label": "Veste vintage marron",
                    "constraints": {"max_price_eur": 50.0, "sizes": ["M"]},
                },
                headers=auth_headers,
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["alert_type"] == "style"
        assert data["status"] == "active"
        assert data["constraints"]["max_price_eur"] == 50.0

    def test_create_specific_item_alert(self, client, user_id, auth_headers):
        with patch("api.routers.alerts.get_conn") as mock_get, \
             patch("api.routers.alerts.put_conn"), \
             patch("api.routers.alerts.count_active_alerts", return_value=1), \
             patch("api.routers.alerts.create_alert") as mock_create:
            mock_get.return_value = _mock_conn()
            mock_create.side_effect = lambda conn, alert: alert

            resp = client.post(
                "/alerts",
                json={
                    "alert_type": "specific_item",
                    "label": "Air Max 90",
                    "reference_product_id": "ebay-42",
                },
                headers=auth_headers,
            )
        assert resp.status_code == 201
        assert resp.json()["reference_product_id"] == "ebay-42"

    def test_free_tier_cap_at_3_active(self, client, user_id, auth_headers):
        with patch("api.routers.alerts.get_conn") as mock_get, \
             patch("api.routers.alerts.put_conn"), \
             patch("api.routers.alerts.count_active_alerts", return_value=3), \
             patch("api.routers.alerts.is_user_premium", return_value=False):
            mock_get.return_value = _mock_conn()

            resp = client.post(
                "/alerts",
                json={"alert_type": "style", "label": "extra"},
                headers=auth_headers,
            )
        assert resp.status_code == 403

    def test_invalid_token_rejected(self, client):
        resp = client.post(
            "/alerts",
            json={"alert_type": "style", "label": "x"},
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        assert resp.status_code in (401, 422)


class TestListAlerts:
    def test_list_returns_alerts(self, client, user_id, auth_headers):
        alerts = [_make_alert(user_id, label="a"), _make_alert(user_id, label="b")]
        with patch("api.routers.alerts.get_conn") as mock_get, \
             patch("api.routers.alerts.put_conn"), \
             patch("api.routers.alerts.list_alerts", return_value=alerts):
            mock_get.return_value = _mock_conn()
            resp = client.get("/alerts", headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["alerts"]) == 2
        assert data["active_count"] == 2
        assert data["free_limit"] == 3

    def test_empty_list(self, client, user_id, auth_headers):
        with patch("api.routers.alerts.get_conn") as mock_get, \
             patch("api.routers.alerts.put_conn"), \
             patch("api.routers.alerts.list_alerts", return_value=[]):
            mock_get.return_value = _mock_conn()
            resp = client.get("/alerts", headers=auth_headers)

        assert resp.status_code == 200
        assert resp.json()["alerts"] == []


class TestPatchAlert:
    def test_pause_alert(self, client, user_id, auth_headers):
        alert = _make_alert(user_id, status=AlertStatus.paused)
        with patch("api.routers.alerts.get_conn") as mock_get, \
             patch("api.routers.alerts.put_conn"), \
             patch("api.routers.alerts.set_alert_status", return_value=True), \
             patch("api.routers.alerts.get_alert", return_value=alert):
            mock_get.return_value = _mock_conn()
            resp = client.patch(
                f"/alerts/{alert.alert_id}",
                json={"status": "paused"},
                headers=auth_headers,
            )
        assert resp.status_code == 200
        assert resp.json()["status"] == "paused"

    def test_patch_not_found(self, client, user_id, auth_headers):
        with patch("api.routers.alerts.get_conn") as mock_get, \
             patch("api.routers.alerts.put_conn"), \
             patch("api.routers.alerts.set_alert_status", return_value=False):
            mock_get.return_value = _mock_conn()
            resp = client.patch(
                f"/alerts/{uuid4()}",
                json={"status": "paused"},
                headers=auth_headers,
            )
        assert resp.status_code == 404


class TestDeleteAlert:
    def test_delete_alert(self, client, user_id, auth_headers):
        alert = _make_alert(user_id)
        with patch("api.routers.alerts.get_conn") as mock_get, \
             patch("api.routers.alerts.put_conn"), \
             patch("api.routers.alerts.delete_alert", return_value=True):
            mock_get.return_value = _mock_conn()
            resp = client.delete(f"/alerts/{alert.alert_id}", headers=auth_headers)
        assert resp.status_code == 204

    def test_delete_not_found(self, client, user_id, auth_headers):
        with patch("api.routers.alerts.get_conn") as mock_get, \
             patch("api.routers.alerts.put_conn"), \
             patch("api.routers.alerts.delete_alert", return_value=False):
            mock_get.return_value = _mock_conn()
            resp = client.delete(f"/alerts/{uuid4()}", headers=auth_headers)
        assert resp.status_code == 404
