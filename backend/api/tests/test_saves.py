"""Tests for the wardrobe endpoint — KAN-89.

"Mon dressing" lived in a React useState: it emptied on every restart and
never reached the server, even though the saves were already being recorded as
InteractionEvents. The list is derived from the event log rather than stored,
so what matters is that the *latest* save/unsave wins.
"""
from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from api.app import app
from api.auth import create_token
from api.db import get_conn, put_conn

pytestmark = pytest.mark.requires_db


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def auth_headers():
    return {"Authorization": f"Bearer {create_token(uuid4())}"}


@pytest.fixture()
def product_ids():
    """Two throwaway products, removed afterwards."""
    ids = [f"saves-test-{uuid4().hex}" for _ in range(2)]
    conn = get_conn()
    with conn.cursor() as cur:
        for index, product_id in enumerate(ids):
            cur.execute(
                "INSERT INTO products (id, source, source_record_id, title,"
                " price, condition, category, image_urls, available)"
                " VALUES (%s, 'ebay', %s, %s, %s, 'good', 'sneakers',"
                " ARRAY['https://example.com/i.jpg'], true)",
                (product_id, product_id, f"Wardrobe item {index}", 30.0 + index),
            )
    conn.commit()
    yield ids
    with conn.cursor() as cur:
        cur.execute("DELETE FROM products WHERE id = ANY(%s)", (ids,))
    conn.commit()
    put_conn(conn)


def _post(client, headers, product_id: str, event_type: str):
    resp = client.post(
        "/events",
        json={"product_id": product_id, "event_type": event_type, "payload": {}},
        headers=headers,
    )
    assert resp.status_code in (200, 201), resp.text


def _wardrobe(client, headers) -> list[str]:
    resp = client.get("/saves", headers=headers)
    assert resp.status_code == 200
    return [p["id"] for p in resp.json()["products"]]


class TestWardrobe:
    def test_starts_empty(self, client, auth_headers):
        assert _wardrobe(client, auth_headers) == []

    def test_a_saved_product_appears(self, client, auth_headers, product_ids):
        _post(client, auth_headers, product_ids[0], "save")
        assert _wardrobe(client, auth_headers) == [product_ids[0]]

    def test_unsaving_removes_it(self, client, auth_headers, product_ids):
        _post(client, auth_headers, product_ids[0], "save")
        _post(client, auth_headers, product_ids[0], "unsave")
        assert _wardrobe(client, auth_headers) == []

    def test_saving_again_after_unsaving_brings_it_back(
        self, client, auth_headers, product_ids,
    ):
        """The latest event wins. Counting saves against unsaves would call
        save/unsave/save a tie and drop the item."""
        _post(client, auth_headers, product_ids[0], "save")
        _post(client, auth_headers, product_ids[0], "unsave")
        _post(client, auth_headers, product_ids[0], "save")
        assert _wardrobe(client, auth_headers) == [product_ids[0]]

    def test_most_recent_save_comes_first(self, client, auth_headers, product_ids):
        _post(client, auth_headers, product_ids[0], "save")
        _post(client, auth_headers, product_ids[1], "save")
        assert _wardrobe(client, auth_headers)[0] == product_ids[1]

    def test_a_swipe_is_not_a_save(self, client, auth_headers, product_ids):
        _post(client, auth_headers, product_ids[0], "swipe_right")
        assert _wardrobe(client, auth_headers) == []

    def test_one_user_does_not_see_another_wardrobe(
        self, client, auth_headers, product_ids,
    ):
        _post(client, auth_headers, product_ids[0], "save")
        other = {"Authorization": f"Bearer {create_token(uuid4())}"}
        assert _wardrobe(client, other) == []

    def test_products_carry_what_the_card_renders(
        self, client, auth_headers, product_ids,
    ):
        _post(client, auth_headers, product_ids[0], "save")
        product = client.get("/saves", headers=auth_headers).json()["products"][0]
        assert product["title"] and product["price"] > 0
        assert product["image_urls"], "a card with no image cannot render"

    def test_requires_authentication(self, client):
        assert client.get("/saves").status_code in (401, 403)
