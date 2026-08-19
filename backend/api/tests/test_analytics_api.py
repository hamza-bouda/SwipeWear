from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from api.app import app
from api.auth import create_token


def _mock_conn() -> MagicMock:
    conn = MagicMock()
    conn.cursor.return_value.__enter__ = lambda current: current
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return conn


def test_analytics_event_is_persisted_for_authenticated_user():
    user_id = uuid4()
    conn = _mock_conn()
    with patch("api.routers.analytics.get_conn", return_value=conn), patch(
        "api.routers.analytics.put_conn"
    ):
        response = TestClient(app).post(
            "/analytics/events",
            json={
                "name": "outbound_click",
                "properties": {"product_id": "item-1", "price": 20},
                "occurred_at": "2026-08-19T12:00:00.000Z",
            },
            headers={"Authorization": f"Bearer {create_token(user_id)}"},
        )

    assert response.status_code == 201
    assert response.json()["accepted"] is True
    assert conn.commit.called
    params = conn.cursor.return_value.execute.call_args.args[1]
    assert params[1] == str(user_id)
    assert params[2] == "outbound_click"


def test_analytics_event_rejects_invalid_name():
    response = TestClient(app).post(
        "/analytics/events",
        json={"name": "Invalid event", "occurred_at": "2026-08-19T12:00:00.000Z"},
        headers={"Authorization": f"Bearer {create_token(uuid4())}"},
    )
    assert response.status_code == 422
