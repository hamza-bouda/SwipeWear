"""Tests for concurrent image prefetching in index_batch — KAN-87.

Downloading inside the encode loop left the CPU idle for roughly two thirds of
every product (~520 ms of network against ~236 ms of encoding), which is the
difference between a 3 h and a 10 h run over 50 000 products.
"""
from __future__ import annotations

import threading
import time

import numpy as np
import pytest

from contracts.product import ProductCondition, ProductRecord, ProductSource
from embeddings.indexer import CatalogueIndexer


class _FakeEmbeddingService:
    embedding_version = "fashionsiglip-v1"
    vector_dim = 768

    def encode_image(self, image: bytes) -> np.ndarray:
        vector = np.zeros(self.vector_dim, dtype=np.float32)
        vector[0] = 1.0
        return vector


class _FakeStore:
    def __init__(self) -> None:
        self.upserted: list[str] = []

    def upsert_embedding(self, product_id, embedding, version, indexed_at) -> None:
        self.upserted.append(product_id)

    def mark_stale_products(self, embedding_version: str) -> int:
        return 0


def _record(index: int) -> ProductRecord:
    return ProductRecord(
        id=f"p{index}",
        source=ProductSource.ebay,
        source_record_id=str(index),
        title=f"Product {index}",
        price=42.0,
        condition=ProductCondition.good,
        category="sneakers",
        image_urls=[f"https://example.com/{index}.jpg"],
    )


def _make_indexer(store, loader) -> CatalogueIndexer:
    return CatalogueIndexer(
        embedding_service=_FakeEmbeddingService(),
        store=store,
        image_loader=loader,
    )


class TestPrefetch:
    def test_every_product_is_indexed_once(self):
        store = _FakeStore()
        records = [_record(i) for i in range(12)]
        result = _make_indexer(
            store, lambda url: b"image-bytes"
        ).index_batch(records, max_workers=4)

        assert result.indexed == 12
        assert result.failed == 0
        assert store.upserted == [r.id for r in records]

    def test_order_is_preserved(self):
        """Downloads finish out of order; embeddings must still line up with
        the record they belong to."""
        store = _FakeStore()

        def loader(url: str) -> bytes:
            # Later URLs resolve faster, so completion order != submit order.
            index = int(url.rsplit("/", 1)[1].split(".")[0])
            time.sleep((10 - index) * 0.005)
            return f"bytes-{index}".encode()

        records = [_record(i) for i in range(10)]
        _make_indexer(store, loader).index_batch(records, max_workers=5)
        assert store.upserted == [r.id for r in records]

    def test_a_failed_download_does_not_stop_the_batch(self):
        store = _FakeStore()

        def loader(url: str) -> bytes:
            if url.endswith("/3.jpg"):
                raise OSError("connection reset")
            return b"image-bytes"

        result = _make_indexer(store, loader).index_batch(
            [_record(i) for i in range(6)], max_workers=3,
        )
        assert result.indexed == 5
        assert result.failed == 1
        assert "p3" in result.failures
        assert "p3" not in store.upserted

    def test_downloads_actually_overlap(self):
        """A serialised implementation would take n * delay; overlapping
        must beat that comfortably."""
        delay = 0.05
        n = 12
        store = _FakeStore()

        def loader(url: str) -> bytes:
            time.sleep(delay)
            return b"image-bytes"

        start = time.monotonic()
        _make_indexer(store, loader).index_batch(
            [_record(i) for i in range(n)], max_workers=6,
        )
        assert time.monotonic() - start < n * delay * 0.6

    def test_look_ahead_is_bounded(self):
        """An unbounded executor.map would submit all 50 000 downloads at once
        and hold the whole catalogue's images in memory."""
        in_flight = 0
        peak = 0
        lock = threading.Lock()

        def loader(url: str) -> bytes:
            nonlocal in_flight, peak
            with lock:
                in_flight += 1
                peak = max(peak, in_flight)
            time.sleep(0.01)
            with lock:
                in_flight -= 1
            return b"image-bytes"

        workers = 4
        _make_indexer(_FakeStore(), loader).index_batch(
            [_record(i) for i in range(60)], max_workers=workers,
        )
        assert peak <= workers

    def test_single_worker_keeps_the_sequential_path(self):
        store = _FakeStore()
        calls: list[str] = []

        def loader(url: str) -> bytes:
            calls.append(url)
            return b"image-bytes"

        result = _make_indexer(store, loader).index_batch(
            [_record(i) for i in range(4)], max_workers=1,
        )
        assert result.indexed == 4
        assert calls == [f"https://example.com/{i}.jpg" for i in range(4)]
