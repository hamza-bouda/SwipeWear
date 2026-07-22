"""KAN-29 integration acceptance test against a live Postgres + pgvector.

The test skips when the local database is unavailable or migration 002 has not
been applied.  It never loads FashionSigLIP or contacts external image hosts.
"""
from __future__ import annotations

import os
from uuid import uuid4

import numpy as np
import pytest

from contracts.product import ProductCondition, ProductRecord, ProductSource
from embeddings.indexer import CatalogueIndexer, PostgresEmbeddingStore

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://swipewear:swipewear_dev@localhost:5432/swipewear",
)


class DeterministicEmbeddingService:
    embedding_version = "kan29-recall-test-v1"
    vector_dim = 768

    def encode_image(self, image: bytes) -> np.ndarray:
        index = int(image.decode())
        vector = np.zeros(self.vector_dim, dtype=np.float32)
        vector[index] = 1.0
        return vector

    def encode_text(self, text: str) -> np.ndarray:
        return self.encode_image(text.encode())


def _connect_or_skip():
    try:
        import psycopg2  # type: ignore[import-untyped]

        connection = psycopg2.connect(DATABASE_URL)
    except Exception as exc:
        pytest.skip(f"Postgres unavailable: {exc}")

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
              FROM information_schema.columns
             WHERE table_name = 'products'
               AND column_name IN ('embedding_version', 'needs_reindex')
            """
        )
        migrated = cursor.fetchone()[0] == 2
    if not migrated:
        connection.close()
        pytest.skip("migration 002_catalog_indexer.sql is not applied")
    return connection


def _vector_literal(vector: np.ndarray) -> str:
    return "[" + ",".join(str(float(value)) for value in vector) + "]"


def test_ten_products_are_indexed_with_recall_at_one_for_three_queries() -> None:
    connection = _connect_or_skip()
    run_id = uuid4().hex
    product_ids = [f"kan29-{run_id}-{index}" for index in range(10)]
    records = [
        ProductRecord(
            id=product_id,
            source=ProductSource.ebay,
            source_record_id=f"source-{run_id}-{index}",
            title=f"KAN-29 product {index}",
            price=20.0 + index,
            condition=ProductCondition.good,
            category="tops",
            image_urls=[f"memory://{index}"],
        )
        for index, product_id in enumerate(product_ids)
    ]

    try:
        with connection:
            with connection.cursor() as cursor:
                for record in records:
                    cursor.execute(
                        """
                        INSERT INTO products (
                            id, source, source_record_id, title, price,
                            condition, category, image_urls
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            record.id,
                            record.source.value,
                            record.source_record_id,
                            record.title,
                            record.price,
                            record.condition.value,
                            record.category,
                            record.image_urls,
                        ),
                    )

        service = DeterministicEmbeddingService()
        result = CatalogueIndexer(
            service,
            PostgresEmbeddingStore(connection),
            lambda url: url.removeprefix("memory://").encode(),
        ).index_batch(records)

        assert result.indexed == 10
        assert result.failed == 0

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                  FROM product_embeddings
                 WHERE product_id = ANY(%s)
                   AND embedding_version = %s
                """,
                (product_ids, service.embedding_version),
            )
            assert cursor.fetchone()[0] == 10

            correct = 0
            for query_index in (1, 5, 8):
                query = service.encode_text(str(query_index))
                cursor.execute(
                    """
                    SELECT product_id
                      FROM product_embeddings
                     WHERE product_id = ANY(%s)
                     ORDER BY embedding <=> %s::vector
                     LIMIT 1
                    """,
                    (product_ids, _vector_literal(query)),
                )
                correct += cursor.fetchone()[0] == product_ids[query_index]

        assert correct / 3 == 1.0
    finally:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM products WHERE id = ANY(%s)",
                    (product_ids,),
                )
        connection.close()
