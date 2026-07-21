from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest

from contracts.product import ProductCondition, ProductRecord, ProductSource
from embeddings.indexer import CatalogueIndexer, index_batch, index_product


class FakeEmbeddingService:
    embedding_version = "test-embedding-v1"
    vector_dim = 512

    def __init__(self) -> None:
        self.images: list[bytes] = []
        self.output = np.ones(512, dtype=np.float32) / np.sqrt(512)

    def encode_image(self, image: bytes) -> np.ndarray:
        self.images.append(image)
        return self.output

    def encode_text(self, text: str) -> np.ndarray:
        return self.output


class FakeStore:
    def __init__(self, *, stale_count: int = 0) -> None:
        self.stale_count = stale_count
        self.marked_versions: list[str] = []
        self.embeddings: dict[str, tuple[np.ndarray, str, datetime]] = {}

    def mark_stale_products(self, embedding_version: str) -> int:
        self.marked_versions.append(embedding_version)
        return self.stale_count

    def upsert_embedding(
        self,
        product_id: str,
        embedding: np.ndarray,
        embedding_version: str,
        indexed_at: datetime,
    ) -> None:
        self.embeddings[product_id] = (
            embedding.copy(),
            embedding_version,
            indexed_at,
        )


def _record(index: int = 0, *, image_count: int = 1) -> ProductRecord:
    return ProductRecord(
        id=f"product-{index}",
        source=ProductSource.ebay,
        source_record_id=f"source-{index}",
        title=f"Fashion product {index}",
        price=20.0 + index,
        condition=ProductCondition.good,
        category="tops",
        image_urls=[f"memory://{index}/{image}" for image in range(image_count)],
    )


def test_index_product_encodes_primary_image_and_upserts_vector() -> None:
    service = FakeEmbeddingService()
    store = FakeStore(stale_count=4)
    loaded_urls: list[str] = []
    now = datetime(2026, 7, 21, 10, 0, tzinfo=timezone.utc)

    def load_image(url: str) -> bytes:
        loaded_urls.append(url)
        return b"primary-image"

    result = CatalogueIndexer(
        service,
        store,
        load_image,
        clock=lambda: now,
    ).index_product(_record(image_count=3))

    assert loaded_urls == ["memory://0/0"]
    assert service.images == [b"primary-image"]
    assert result.product_id == "product-0"
    assert result.embedding_version == "test-embedding-v1"
    assert result.vector_dim == 512
    assert result.indexed_at == now
    vector, version, indexed_at = store.embeddings["product-0"]
    assert vector.shape == (512,)
    assert version == "test-embedding-v1"
    assert indexed_at == now


def test_public_index_product_accepts_injected_adapters() -> None:
    service = FakeEmbeddingService()
    store = FakeStore()

    result = index_product(
        _record(),
        embedding_service=service,
        store=store,
        image_loader=lambda _: b"image",
    )

    assert result.product_id == "product-0"
    assert set(store.embeddings) == {"product-0"}


def test_index_batch_stores_ten_vectors_and_logs_progress(
    caplog: pytest.LogCaptureFixture,
) -> None:
    service = FakeEmbeddingService()
    store = FakeStore(stale_count=10)
    records = [_record(index) for index in range(10)]

    with caplog.at_level(logging.INFO, logger="swipewear.embeddings.indexer"):
        result = index_batch(
            records,
            embedding_service=service,
            store=store,
            image_loader=lambda url: url.encode(),
        )

    assert result.attempted == 10
    assert result.indexed == 10
    assert result.failed == 0
    assert result.marked_for_reindex == 10
    assert len(store.embeddings) == 10
    assert "Indexed product 10/10: product-9" in caplog.text
    assert "Catalogue indexing complete" in caplog.text


def test_embedding_version_check_runs_once_per_indexer() -> None:
    service = FakeEmbeddingService()
    store = FakeStore(stale_count=3)
    indexer = CatalogueIndexer(service, store, lambda _: b"image")

    indexer.index_product(_record(1))
    indexer.index_product(_record(2))

    assert store.marked_versions == ["test-embedding-v1"]


def test_batch_continues_after_one_product_fails() -> None:
    service = FakeEmbeddingService()
    store = FakeStore()

    def load_image(url: str) -> bytes:
        if url.startswith("memory://2/"):
            raise OSError("image unavailable")
        return url.encode()

    result = CatalogueIndexer(service, store, load_image).index_batch(
        [_record(index) for index in range(5)]
    )

    assert result.attempted == 5
    assert result.indexed == 4
    assert result.failed == 1
    assert result.failures == {"product-2": "OSError: image unavailable"}
    assert set(store.embeddings) == {
        "product-0",
        "product-1",
        "product-3",
        "product-4",
    }


@pytest.mark.parametrize(
    ("output", "message"),
    [
        (np.ones(511, dtype=np.float32), "expected embedding shape"),
        (np.full(512, np.nan, dtype=np.float32), "non-finite"),
    ],
)
def test_invalid_embedding_is_not_persisted(
    output: np.ndarray,
    message: str,
) -> None:
    service = FakeEmbeddingService()
    service.output = output
    store = FakeStore()

    with pytest.raises(ValueError, match=message):
        CatalogueIndexer(service, store, lambda _: b"image").index_product(_record())

    assert store.embeddings == {}


def test_indexer_module_does_not_need_a_real_image_file(tmp_path: Path) -> None:
    """Guard that adapter injection keeps deterministic tests fully offline."""
    image = tmp_path / "image.jpg"
    image.write_bytes(b"fake-image")
    store = FakeStore()

    result = CatalogueIndexer(
        FakeEmbeddingService(),
        store,
        lambda _: image.read_bytes(),
    ).index_product(_record())

    assert result.product_id in store.embeddings


def test_enabled_segmentation_crop_replaces_original_before_encoding() -> None:
    service = FakeEmbeddingService()
    store = FakeStore()
    transformed: list[bytes] = []

    def isolate(image: bytes) -> bytes:
        transformed.append(image)
        return b"isolated-garment-crop"

    CatalogueIndexer(
        service,
        store,
        lambda _: b"whole-person-photo",
        image_transform=isolate,
    ).index_product(_record())

    assert transformed == [b"whole-person-photo"]
    assert service.images == [b"isolated-garment-crop"]


def test_indexer_uses_original_if_image_transform_raises() -> None:
    service = FakeEmbeddingService()
    store = FakeStore()

    def failing_transform(image: bytes) -> bytes:
        raise RuntimeError("segmentation unavailable")

    CatalogueIndexer(
        service,
        store,
        lambda _: b"whole-person-photo",
        image_transform=failing_transform,
    ).index_product(_record())

    assert service.images == [b"whole-person-photo"]
