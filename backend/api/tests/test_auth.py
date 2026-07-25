"""Tests for auth: register, login, delete account, anonymous→signup migration."""
from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from api.app import app
from api.auth import create_token
from api import store


@pytest.fixture(autouse=True)
def _clean_store():
    store.reset()
    yield
    store.reset()


@pytest.fixture()
def client():
    return TestClient(app)


class TestRegister:
    def test_register_success(self, client):
        resp = client.post(
            "/auth/register",
            json={"email": "alice@example.com", "password": "securepass123"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == "alice@example.com"
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["profile_migrated"] is False

    def test_register_duplicate_email(self, client):
        client.post(
            "/auth/register",
            json={"email": "alice@example.com", "password": "securepass123"},
        )
        resp = client.post(
            "/auth/register",
            json={"email": "alice@example.com", "password": "otherpass999"},
        )
        assert resp.status_code == 409

    def test_register_case_insensitive_email(self, client):
        client.post(
            "/auth/register",
            json={"email": "Alice@Example.COM", "password": "securepass123"},
        )
        resp = client.post(
            "/auth/register",
            json={"email": "alice@example.com", "password": "otherpass999"},
        )
        assert resp.status_code == 409

    def test_register_password_too_short(self, client):
        resp = client.post(
            "/auth/register",
            json={"email": "bob@example.com", "password": "short"},
        )
        assert resp.status_code == 422


class TestLogin:
    def test_login_success(self, client):
        client.post(
            "/auth/register",
            json={"email": "alice@example.com", "password": "securepass123"},
        )
        resp = client.post(
            "/auth/login",
            json={"email": "alice@example.com", "password": "securepass123"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == "alice@example.com"
        assert "access_token" in body

    def test_login_wrong_password(self, client):
        client.post(
            "/auth/register",
            json={"email": "alice@example.com", "password": "securepass123"},
        )
        resp = client.post(
            "/auth/login",
            json={"email": "alice@example.com", "password": "wrongpass999"},
        )
        assert resp.status_code == 401

    def test_login_nonexistent_email(self, client):
        resp = client.post(
            "/auth/login",
            json={"email": "nobody@example.com", "password": "whatever123"},
        )
        assert resp.status_code == 401


@pytest.fixture()
def catalogue_product_id():
    """A product id that exists — interaction_events references products."""
    from api.db import get_conn, put_conn

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM products WHERE available = true LIMIT 1")
            row = cur.fetchone()
    finally:
        put_conn(conn)
    if row is None:
        pytest.skip("catalogue is empty — run scripts/ingest_catalogue.py")
    return row[0]


@pytest.mark.requires_db
class TestDeleteAccount:
    def test_delete_account(self, client):
        reg = client.post(
            "/auth/register",
            json={"email": "alice@example.com", "password": "securepass123"},
        )
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.delete("/auth/account", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True

        login_resp = client.post(
            "/auth/login",
            json={"email": "alice@example.com", "password": "securepass123"},
        )
        assert login_resp.status_code == 401

    def test_delete_removes_profile_and_events(self, client, catalogue_product_id):
        reg = client.post(
            "/auth/register",
            json={"email": "alice@example.com", "password": "securepass123"},
        )
        body = reg.json()
        token = body["access_token"]
        user_id = body["user_id"]
        headers = {"Authorization": f"Bearer {token}"}

        client.post(
            "/onboarding/styles",
            json={"liked_brands": ["Nike"], "sizes": ["M"]},
            headers=headers,
        )
        client.post(
            "/events",
            json={
                "product_id": catalogue_product_id,
                "event_type": "swipe_right",
                "payload": {"brand": "Nike"},
            },
            headers=headers,
        )

        client.delete("/auth/account", headers=headers)

        from uuid import UUID
        assert store.get_user(UUID(user_id)) is None
        assert len(store.get_events_for_user(UUID(user_id))) == 0

    def test_delete_unauthenticated(self, client):
        resp = client.delete("/auth/account")
        assert resp.status_code == 422


class TestAnonymousToSignup:
    def test_anonymous_profile_migrated_on_register(self, client):
        anon_id = uuid4()
        anon_token = create_token(anon_id)
        anon_headers = {"Authorization": f"Bearer {anon_token}"}

        client.post(
            "/onboarding/styles",
            json={"liked_brands": ["Carhartt"], "sizes": ["L"], "max_price_eur": 120.0},
            headers=anon_headers,
        )

        profile_resp = client.get("/profile", headers=anon_headers)
        assert profile_resp.json()["hard_constraints"]["sizes"] == ["L"]

        reg = client.post(
            "/auth/register",
            json={
                "email": "alice@example.com",
                "password": "securepass123",
                "anonymous_user_id": str(anon_id),
            },
        )
        assert reg.status_code == 200
        body = reg.json()
        assert body["profile_migrated"] is True

        new_headers = {"Authorization": f"Bearer {body['access_token']}"}
        migrated = client.get("/profile", headers=new_headers)
        assert migrated.json()["hard_constraints"]["sizes"] == ["L"]
        assert migrated.json()["hard_constraints"]["max_price_eur"] == 120.0

    def test_register_without_anonymous_id(self, client):
        reg = client.post(
            "/auth/register",
            json={"email": "bob@example.com", "password": "securepass123"},
        )
        assert reg.status_code == 200
        assert reg.json()["profile_migrated"] is False
