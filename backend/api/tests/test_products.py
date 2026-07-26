"""Tests for GET /products/{id} — KAN-90.

ProductDetailScreen fell back to a hardcoded MOCK_PRODUCTS list whenever it was
opened without a product in hand — from the wardrobe, an alert, or a deep link.
It showed an invented item under a real id, at a price nobody could pay.
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
def product_id():
    """An id shaped like the real ones — the pipes are the interesting part."""
    pid = f"ebay-v1|{uuid4().hex[:12]}|0"
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO products (id, source, source_record_id, title, price,"
            " condition, category, image_urls, size_raw, listing_url, available)"
            " VALUES (%s, 'ebay', %s, 'Veste de test', 42.50, 'good', 'vestes',"
            " ARRAY['https://example.com/i.jpg'], 'M',"
            " 'https://www.ebay.fr/itm/123', true)",
            (pid, pid),
        )
    conn.commit()
    yield pid
    with conn.cursor() as cur:
        cur.execute("DELETE FROM products WHERE id = %s", (pid,))
    conn.commit()
    put_conn(conn)


class TestGetProduct:
    def test_returns_the_product(self, client, auth_headers, product_id):
        resp = client.get(f"/products/{product_id}", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == product_id
        assert body["title"] == "Veste de test"
        assert body["price"] == 42.50

    def test_an_id_containing_pipes_resolves(self, client, auth_headers, product_id):
        """Catalogue ids look like "ebay-v1|127396173312|428490506"; without a
        path converter every caller would have to escape them."""
        assert "|" in product_id
        assert client.get(
            f"/products/{product_id}", headers=auth_headers,
        ).status_code == 200

    def test_the_buy_link_reaches_the_client(self, client, auth_headers, product_id):
        body = client.get(f"/products/{product_id}", headers=auth_headers).json()
        assert body["affiliate_url"] == "https://www.ebay.fr/itm/123"

    def test_an_unknown_id_is_404_not_a_substitute(self, client, auth_headers):
        """The whole point: absent means absent, never an invented product."""
        resp = client.get("/products/does-not-exist", headers=auth_headers)
        assert resp.status_code == 404

    def test_requires_authentication(self, client, product_id):
        assert client.get(f"/products/{product_id}").status_code == 401

    def test_carries_what_the_detail_screen_renders(
        self, client, auth_headers, product_id,
    ):
        body = client.get(f"/products/{product_id}", headers=auth_headers).json()
        assert body["image_urls"], "the gallery cannot render without images"
        assert body["condition"] and body["category"]
        assert body["size_raw"] == "M"
