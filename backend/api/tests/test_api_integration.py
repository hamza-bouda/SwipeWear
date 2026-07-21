"""Integration test: full onboarding → feed → swipe → updated feed scenario."""
from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from api.app import app
from api.auth import create_token
from api import store
from api import trace_store


@pytest.fixture(autouse=True)
def _clean_store():
    store.reset()
    trace_store.reset()
    yield
    store.reset()
    trace_store.reset()


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def user_id():
    return uuid4()


@pytest.fixture()
def auth_headers(user_id):
    token = create_token(user_id)
    return {"Authorization": f"Bearer {token}"}


class TestHealthCheck:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestAuthToken:
    def test_issue_token(self, client, user_id):
        resp = client.post("/auth/token", json={"user_id": str(user_id)})
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_missing_auth_header(self, client):
        resp = client.get("/feed")
        assert resp.status_code == 422

    def test_invalid_token(self, client):
        resp = client.get("/feed", headers={"Authorization": "Bearer bad.token.here"})
        assert resp.status_code == 401


class TestOnboarding:
    def test_post_styles(self, client, auth_headers, user_id):
        resp = client.post(
            "/onboarding/styles",
            json={
                "liked_brands": ["Nike", "Carhartt"],
                "sizes": ["M", "L"],
                "max_price_eur": 100.0,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["user_id"] == str(user_id)
        assert body["profile_initialized"] is True

    def test_post_images(self, client, auth_headers, user_id):
        resp = client.post(
            "/onboarding/images",
            json={"image_urls": ["https://example.com/img1.jpg"]},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["profile_initialized"] is True


class TestProfile:
    def test_get_profile_cold_start(self, client, auth_headers, user_id):
        resp = client.get("/profile", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["user_id"] == str(user_id)
        assert body["is_cold_start"] is True
        assert body["event_count"] == 0

    def test_patch_profile(self, client, auth_headers, user_id):
        resp = client.patch(
            "/profile",
            json={
                "hard_constraints": {"sizes": ["S"], "max_price_eur": 50.0},
                "editable_preferences": {"liked_brands": ["Stussy"]},
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["hard_constraints"]["sizes"] == ["S"]
        assert body["hard_constraints"]["max_price_eur"] == 50.0
        assert body["editable_preferences"]["liked_brands"] == ["Stussy"]


class TestFeed:
    def test_get_feed_default(self, client, auth_headers):
        resp = client.get("/feed", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) == 8
        assert body["next_cursor"] is None
        assert body["items"][0]["explanation"]["grounded"] is False
        assert body["items"][0]["explanation"]["editable_tags"]

    def test_get_feed_paginated(self, client, auth_headers):
        resp = client.get("/feed?n_results=3", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) == 3
        assert body["next_cursor"] == "3"

        resp2 = client.get(f"/feed?n_results=3&cursor={body['next_cursor']}", headers=auth_headers)
        body2 = resp2.json()
        assert len(body2["items"]) == 3
        assert body2["next_cursor"] == "6"

    def test_feed_exposes_owner_only_debug_trace(self, client, auth_headers):
        feed = client.get("/feed", headers=auth_headers)
        trace_id = feed.headers["x-trace-id"]
        trace = client.get(f"/debug/trace/{trace_id}", headers=auth_headers)

        assert trace.status_code == 200
        assert trace.json()["trace_id"] == trace_id


class TestEvents:
    def test_post_swipe_right(self, client, auth_headers, user_id):
        resp = client.post(
            "/events",
            json={
                "product_id": "prod-1",
                "event_type": "swipe_right",
                "payload": {"brand": "Nike"},
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["accepted"] is True
        assert "event_id" in body

    def test_swipe_updates_profile(self, client, auth_headers, user_id):
        client.post(
            "/events",
            json={
                "product_id": "prod-1",
                "event_type": "swipe_right",
                "payload": {"brand": "Nike"},
            },
            headers=auth_headers,
        )
        resp = client.get("/profile", headers=auth_headers)
        body = resp.json()
        assert "Nike" in body["editable_preferences"]["liked_brands"]
        assert body["event_count"] == 1
        assert body["is_cold_start"] is False

    def test_swipe_left_style_rejects_brand(self, client, auth_headers, user_id):
        client.post(
            "/events",
            json={
                "product_id": "prod-6",
                "event_type": "swipe_left_style",
                "payload": {"brand": "Stussy"},
            },
            headers=auth_headers,
        )
        resp = client.get("/profile", headers=auth_headers)
        body = resp.json()
        assert "Stussy" in body["editable_preferences"]["rejected_brands"]


class TestFullScenario:
    """Full integration: onboarding → feed → swipe → profile updated."""

    def test_complete_flow(self, client, user_id):
        token_resp = client.post("/auth/token", json={"user_id": str(user_id)})
        token = token_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        client.post(
            "/onboarding/styles",
            json={"liked_brands": ["Nike"], "sizes": ["M"], "max_price_eur": 80.0},
            headers=headers,
        )

        feed_resp = client.get("/feed?n_results=3", headers=headers)
        assert feed_resp.status_code == 200
        items = feed_resp.json()["items"]
        assert len(items) == 3
        first_product_id = items[0]["product"]["id"]

        client.post(
            "/events",
            json={
                "product_id": first_product_id,
                "event_type": "swipe_right",
                "payload": {"brand": items[0]["product"].get("brand", "")},
            },
            headers=headers,
        )

        profile_resp = client.get("/profile", headers=headers)
        profile = profile_resp.json()
        assert profile["event_count"] == 1
        assert profile["is_cold_start"] is False
        assert profile["hard_constraints"]["sizes"] == ["M"]
        assert profile["hard_constraints"]["max_price_eur"] == 80.0

        feed_resp2 = client.get(
            f"/feed?n_results=3&cursor={feed_resp.json()['next_cursor']}",
            headers=headers,
        )
        assert feed_resp2.status_code == 200
        assert len(feed_resp2.json()["items"]) == 3
