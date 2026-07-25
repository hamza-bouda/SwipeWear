"""Tests for the indexer's needs_reindex reconciliation — KAN-88.

needs_reindex is global mutable state: mark_stale_products rewrites it across
the whole table, so a single process running under a different embedding
version flags the entire catalogue as stale. That happened for real — an
integration test using its own version flipped 7 385 already-indexed products
back, which on a multi-hour run means re-encoding work already done.
"""
from __future__ import annotations

from uuid import uuid4

import pytest

from api.db import get_conn, put_conn
from scripts.run_indexer import _reconcile_flags

pytestmark = pytest.mark.requires_db

_CURRENT = "fashionsiglip-v1"


@pytest.fixture()
def product():
    """A throwaway product with a current-version embedding, marked stale."""
    product_id = f"reconcile-test-{uuid4().hex}"
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO products (id, source, source_record_id, title, price,"
            " condition, category, image_urls, embedding_version, needs_reindex)"
            " VALUES (%s, 'ebay', %s, 'Test', 10.0, 'good', 'sneakers',"
            " ARRAY['https://example.com/i.jpg'], %s, TRUE)",
            (product_id, product_id, _CURRENT),
        )
        cur.execute(
            "INSERT INTO product_embeddings"
            " (product_id, embedding, embedding_version, indexed_at)"
            " VALUES (%s, %s::vector, %s, NOW())",
            (product_id, "[" + ",".join(["0.1"] * 768) + "]", _CURRENT),
        )
    conn.commit()
    yield conn, product_id
    with conn.cursor() as cur:
        cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
    conn.commit()
    put_conn(conn)


def _needs_reindex(conn, product_id: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT needs_reindex FROM products WHERE id = %s", (product_id,),
        )
        return cur.fetchone()[0]


def test_a_product_with_a_current_embedding_is_cleared(product):
    conn, product_id = product
    assert _needs_reindex(conn, product_id) is True

    _reconcile_flags(conn, _CURRENT)

    assert _needs_reindex(conn, product_id) is False


def test_a_version_bump_leaves_older_embeddings_marked(product):
    """The dangerous mistake would be clearing the flag whenever product and
    embedding agree — that would silently cancel a legitimate re-index after
    the model changes."""
    conn, product_id = product

    _reconcile_flags(conn, "fashionsiglip-v2")

    assert _needs_reindex(conn, product_id) is True


def test_reconciling_twice_changes_nothing_the_second_time(product):
    conn, product_id = product

    first = _reconcile_flags(conn, _CURRENT)
    second = _reconcile_flags(conn, _CURRENT)

    assert first >= 1
    assert second == 0


def test_a_product_without_an_embedding_stays_marked(product):
    conn, _ = product
    orphan = f"reconcile-orphan-{uuid4().hex}"
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO products (id, source, source_record_id, title, price,"
            " condition, category, image_urls, embedding_version, needs_reindex)"
            " VALUES (%s, 'ebay', %s, 'Test', 10.0, 'good', 'sneakers',"
            " ARRAY['https://example.com/i.jpg'], %s, TRUE)",
            (orphan, orphan, _CURRENT),
        )
    conn.commit()
    try:
        _reconcile_flags(conn, _CURRENT)
        assert _needs_reindex(conn, orphan) is True
    finally:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM products WHERE id = %s", (orphan,))
        conn.commit()
