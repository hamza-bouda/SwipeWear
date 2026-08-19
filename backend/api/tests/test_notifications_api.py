from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from api.app import app
from api.auth import create_token


def test_opened_notification_is_scoped_to_authenticated_user():
    user_id = uuid4()
    conn = MagicMock()
    with patch("api.routers.notifications.get_conn", return_value=conn), patch(
        "api.routers.notifications.put_conn"
    ), patch("api.routers.notifications.mark_notification_opened") as mark_opened:
        response = TestClient(app).post(
            "/notifications/opened",
            json={"queue_id": str(uuid4())},
            headers={"Authorization": f"Bearer {create_token(user_id)}"},
        )

    assert response.status_code == 204
    assert mark_opened.call_args.args[2] == user_id
