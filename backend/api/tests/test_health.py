"""Tests for the /health probe — KAN-88.

railway.toml points its healthcheck at /health, which used to return
{"status": "ok"} unconditionally. A deployment whose database was unreachable
or misconfigured was therefore declared healthy and put in front of users.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi import Response

from api.app import health


def _stub_conn(rows: list | None = None) -> MagicMock:
    cursor = MagicMock()
    cursor.__enter__ = lambda s: s
    cursor.__exit__ = MagicMock(return_value=False)
    cursor.fetchone.side_effect = rows or [(1,)]
    conn = MagicMock()
    conn.cursor.return_value = cursor
    return conn


class TestHealthy:
    def test_reports_ok_when_the_database_answers(self):
        response = Response()
        with patch("api.app.get_conn", return_value=_stub_conn()), \
                patch("api.app.put_conn"):
            body = health(response)
        assert response.status_code == 200
        assert body["status"] == "ok"
        assert body["checks"]["database"] is True

    def test_reports_the_environment_and_version(self):
        response = Response()
        with patch("api.app.get_conn", return_value=_stub_conn()), \
                patch("api.app.put_conn"), \
                patch("api.app.app_env", return_value="production"):
            body = health(response)
        assert body["environment"] == "production"
        assert body["version"]

    def test_connection_is_returned_to_the_pool(self):
        """A probe that leaks a connection on every call drains the pool."""
        conn = _stub_conn()
        with patch("api.app.get_conn", return_value=conn), \
                patch("api.app.put_conn") as put:
            health(Response())
        put.assert_called_once_with(conn)


class TestUnhealthy:
    def test_returns_503_when_the_database_is_unreachable(self):
        response = Response()
        with patch("api.app.get_conn", side_effect=OSError("connection refused")), \
                patch("api.app.put_conn"):
            body = health(response)
        assert response.status_code == 503
        assert body["status"] == "degraded"
        assert body["checks"]["database"] is False

    def test_returns_503_when_the_query_fails(self):
        """Reachable but broken — a pool handing out dead connections still
        cannot serve a request."""
        conn = MagicMock()
        conn.cursor.side_effect = RuntimeError("server closed the connection")
        response = Response()
        with patch("api.app.get_conn", return_value=conn), \
                patch("api.app.put_conn"):
            body = health(response)
        assert response.status_code == 503
        assert body["checks"]["database"] is False

    def test_connection_is_returned_even_when_the_check_fails(self):
        conn = MagicMock()
        conn.cursor.side_effect = RuntimeError("boom")
        with patch("api.app.get_conn", return_value=conn), \
                patch("api.app.put_conn") as put:
            health(Response())
        put.assert_called_once_with(conn)


class TestDeepProbe:
    def test_deep_reports_catalogue_counts(self):
        conn = _stub_conn(rows=[(1,), (50_870,), (2_827,)])
        with patch("api.app.get_conn", return_value=conn), \
                patch("api.app.put_conn"):
            body = health(Response(), deep=True)
        assert body["details"]["products_available"] == 50_870
        assert body["details"]["products_indexed"] == 2_827

    def test_default_probe_stays_cheap(self):
        """The probe runs constantly; counting a 50k table on every call is
        not something a liveness check should be doing."""
        conn = _stub_conn()
        with patch("api.app.get_conn", return_value=conn), \
                patch("api.app.put_conn"):
            body = health(Response())
        assert "details" not in body
        conn.cursor.return_value.execute.assert_called_once_with("SELECT 1")
