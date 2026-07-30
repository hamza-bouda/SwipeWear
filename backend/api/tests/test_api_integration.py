"""Integration test: full onboarding → feed → swipe → updated feed scenario."""
from __future__ import annotations

from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from api.app import app
from api.auth import create_anonymous_token
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
    token = create_anonymous_token(user_id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def catalogue_product_ids(database_available):
    """Two product ids that actually exist in the catalogue.

    interaction_events.product_id is a foreign key onto products, so the
    invented "prod-1" these tests used to post could only ever work against
    the in-memory store they were written for.
    """
    if not database_available:
        pytest.skip("no reachable PostgreSQL instance")
    from api.db import get_conn, put_conn

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM products WHERE available = true LIMIT 2")
            rows = cur.fetchall()
    finally:
        put_conn(conn)
    if len(rows) < 2:
        pytest.skip("catalogue is empty — run scripts/ingest_catalogue.py")
    return [row[0] for row in rows]


class TestHealthCheck:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestAuthToken:
    def test_issue_anonymous_session(self, client):
        resp = client.post("/auth/anonymous")
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        # The server picks the identity. The endpoint this replaced signed a
        # caller-supplied user_id, which was an account takeover.
        assert UUID(body["user_id"])

    def test_missing_auth_header(self, client):
        """401, not 422 — see get_current_user_id."""
        resp = client.get("/feed")
        assert resp.status_code == 401

    def test_invalid_token(self, client):
        resp = client.get("/feed", headers={"Authorization": "Bearer bad.token.here"})
        assert resp.status_code == 401


class TestOnboarding:
    def test_post_styles(self, client, auth_headers, user_id):
        resp = client.post(
            "/onboarding/styles",
            json={
                "style_ids": ["streetwear", "techwear"],
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

        profile_resp = client.get("/profile", headers=auth_headers)
        assert profile_resp.json()["is_cold_start"] is False

    def test_post_images(self, client, auth_headers, user_id, monkeypatch):
        fake_service = MagicMock()
        fake_service.encode_image.return_value = [1.0, 0.0, 0.0, 0.0]
        monkeypatch.setattr("api.routers.onboarding.get_service", lambda: fake_service)
        monkeypatch.setattr(
            "api.routers.onboarding.download_image", lambda url: b"fake-image-bytes"
        )

        resp = client.post(
            "/onboarding/images",
            json={"image_urls": ["https://example.com/img1.jpg"]},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["profile_initialized"] is True

        profile_resp = client.get("/profile", headers=auth_headers)
        assert profile_resp.json()["is_cold_start"] is False

    def test_post_images_unreachable_url_does_not_crash(
        self, client, auth_headers, monkeypatch
    ):
        def _raise(url):
            raise ConnectionError("boom")

        monkeypatch.setattr("api.routers.onboarding.get_service", lambda: MagicMock())
        monkeypatch.setattr("api.routers.onboarding.download_image", _raise)

        resp = client.post(
            "/onboarding/images",
            json={"image_urls": ["https://example.com/broken.jpg"]},
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


class TestPreferencesApi:
    def test_add_list_lock_unlock_and_delete_preference(self, client, auth_headers):
        created = client.post(
            "/profile/preferences",
            json={"attribute": "liked_brands", "value": "Carhartt"},
            headers=auth_headers,
        )
        assert created.status_code == 201
        preference_id = created.json()["preference"]["id"]

        listed = client.get("/profile/preferences", headers=auth_headers)
        assert listed.status_code == 200
        assert listed.json()["preferences"][0]["source"] == "edited"

        locked = client.post(
            f"/profile/preferences/{preference_id}/lock", headers=auth_headers,
        )
        assert locked.json()["preference"]["locked"] is True
        unlocked = client.post(
            f"/profile/preferences/{preference_id}/unlock", headers=auth_headers,
        )
        assert unlocked.json()["preference"]["locked"] is False

        deleted = client.delete(f"/profile/preferences/{preference_id}", headers=auth_headers)
        assert deleted.status_code == 204
        assert client.get("/profile/preferences", headers=auth_headers).json()["preferences"] == []


@pytest.fixture()
def stocked_catalogue():
    """Put a handful of products in the catalogue, and take them out after.

    These tests read whatever the database happened to contain, so they passed
    on a developer machine holding 50 000 ingested products and failed on CI's
    empty one. A test that depends on ambient data is not testing the feed, it
    is testing the machine — so it brings its own.
    """
    from api.db import get_conn, put_conn

    ids = [f"feedtest-{uuid4().hex}" for _ in range(5)]
    conn = get_conn()
    with conn.cursor() as cur:
        for index, product_id in enumerate(ids):
            cur.execute(
                "INSERT INTO products (id, source, source_record_id, title,"
                " price, condition, category, image_urls, size_eu, available)"
                " VALUES (%s, 'ebay', %s, %s, %s, 'good', 'sneakers',"
                " ARRAY['https://example.com/i.jpg'], 'M', true)",
                (product_id, product_id, f"Test sneaker {index}", 40.0 + index),
            )
    conn.commit()
    yield ids
    with conn.cursor() as cur:
        cur.execute("DELETE FROM products WHERE id = ANY(%s)", (ids,))
    conn.commit()
    put_conn(conn)


@pytest.mark.requires_db
@pytest.mark.usefixtures("stocked_catalogue")
class TestFeed:
    """Exercises the real pipeline.

    These assertions used to hardcode the shape of the mock feed (exactly 8
    items, next_cursor "3"), so they only passed while the database was
    unreachable — they were testing the fallback fiction, not the feed. They
    now describe the contract the API actually owes a client.
    """

    def test_get_feed_returns_real_catalogue_products(self, client, auth_headers):
        resp = client.get("/feed", headers=auth_headers)
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert items, "the feed must not come back empty on a stocked catalogue"
        assert not any(
            item["product"]["id"].startswith("prod-") for item in items
        ), "mock products leaked into a real feed response"

    def test_every_item_carries_what_the_client_renders(self, client, auth_headers):
        items = client.get("/feed?n_results=5", headers=auth_headers).json()["items"]
        for item in items:
            product = item["product"]
            assert product["id"] and product["title"]
            assert product["price"] > 0
            assert product["image_urls"], "a card with no image cannot render"
            assert item["explanation"]["editable_tags"]

    def test_n_results_is_honoured(self, client, auth_headers):
        body = client.get("/feed?n_results=3", headers=auth_headers).json()
        assert len(body["items"]) <= 3

    def test_ranks_are_contiguous_and_ordered(self, client, auth_headers):
        items = client.get("/feed?n_results=10", headers=auth_headers).json()["items"]
        assert [i["rank"] for i in items] == list(range(1, len(items) + 1))

    @pytest.mark.requires_db
    def test_feed_exposes_owner_only_debug_trace(self, client, auth_headers):
        feed = client.get("/feed", headers=auth_headers)
        trace_id = feed.headers["x-trace-id"]
        trace = client.get(f"/debug/trace/{trace_id}", headers=auth_headers)

        assert trace.status_code == 200
        assert trace.json()["trace_id"] == trace_id


@pytest.mark.requires_db
class TestEvents:
    def test_post_swipe_right(self, client, auth_headers, catalogue_product_ids):
        resp = client.post(
            "/events",
            json={
                "product_id": catalogue_product_ids[0],
                "event_type": "swipe_right",
                "payload": {"brand": "Nike"},
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["accepted"] is True
        assert "event_id" in body

    def test_swipe_updates_profile(self, client, auth_headers, catalogue_product_ids):
        client.post(
            "/events",
            json={
                "product_id": catalogue_product_ids[0],
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

    def test_swipe_left_style_rejects_brand(self, client, auth_headers, catalogue_product_ids):
        client.post(
            "/events",
            json={
                "product_id": catalogue_product_ids[1],
                "event_type": "swipe_left_style",
                "payload": {"brand": "Stussy"},
            },
            headers=auth_headers,
        )
        resp = client.get("/profile", headers=auth_headers)
        body = resp.json()
        assert "Stussy" in body["editable_preferences"]["rejected_brands"]


@pytest.mark.requires_db
@pytest.mark.usefixtures("stocked_catalogue")
class TestFullScenario:
    """Full integration: onboarding → feed → swipe → profile updated."""

    def test_complete_flow(self, client, user_id):
        token_resp = client.post("/auth/anonymous")
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
        assert 0 < len(items) <= 3
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
