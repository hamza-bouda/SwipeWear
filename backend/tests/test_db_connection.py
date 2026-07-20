"""Integration tests — require a live Postgres+pgvector instance.

Run after `docker-compose up`:
    pytest tests/test_db_connection.py

These tests are NOT included in pyproject.toml testpaths so they do not
run automatically in CI (which has no Docker service).  They skip gracefully
when the database is unreachable.
"""
from __future__ import annotations

import os

import pytest

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://swipewear:swipewear_dev@localhost:5432/swipewear",
)


def _try_connect():
    try:
        import psycopg2
        return psycopg2.connect(DATABASE_URL)
    except Exception:
        return None


@pytest.fixture(scope="module")
def conn():
    c = _try_connect()
    if c is None:
        pytest.skip("Postgres unreachable — run `docker-compose up` first")
    yield c
    c.close()


class TestConnection:
    def test_postgres_reachable(self, conn):
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            assert cur.fetchone() == (1,)

    def test_pgvector_extension_installed(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "SELECT extname FROM pg_extension WHERE extname = 'vector'"
            )
            row = cur.fetchone()
        assert row is not None, "pgvector extension not found — check migrations"


class TestSchema:
    def test_required_tables_exist(self, conn):
        required = {
            "products",
            "product_embeddings",
            "interaction_events",
            "user_profiles",
        }
        with conn.cursor() as cur:
            cur.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
            )
            present = {row[0] for row in cur.fetchall()}
        missing = required - present
        assert not missing, f"Missing tables: {missing}"

    def test_hnsw_index_exists(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "SELECT indexname FROM pg_indexes"
                " WHERE tablename = 'product_embeddings'"
            )
            indexes = {row[0] for row in cur.fetchall()}
        assert "idx_product_embeddings_hnsw" in indexes

    def test_embedding_column_is_512_dims(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "SELECT a.atttypmod"
                " FROM pg_attribute a"
                " JOIN pg_class c ON c.oid = a.attrelid"
                " WHERE c.relname = 'product_embeddings'"
                "   AND a.attname = 'embedding'"
            )
            row = cur.fetchone()
        assert row is not None, "Column 'embedding' not found in product_embeddings"
        assert row[0] == 512, f"Expected 512 dims, got {row[0]}"

    def test_interaction_events_user_index_exists(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "SELECT indexname FROM pg_indexes"
                " WHERE tablename = 'interaction_events'"
            )
            indexes = {row[0] for row in cur.fetchall()}
        assert "idx_interaction_events_user_time" in indexes
