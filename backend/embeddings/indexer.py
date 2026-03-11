"""Catalogue indexing pipeline for FashionSigLIP embeddings.

The public ``index_product`` and ``index_batch`` helpers use PostgreSQL by
default.  Their dependencies are injectable so unit tests and offline jobs do
not need to load the real model or contact an image host.
"""
from __future__ import annotations

import logging
import os
from collections import deque
from collections.abc import Callable, Iterator, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from itertools import islice
from typing import Any, Protocol

import numpy as np
import requests  # type: ignore[import-untyped]

from contracts.product import ProductRecord
from embeddings.interfaces import EmbeddingService

_LOG = logging.getLogger("swipewear.embeddings.indexer")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://swipewear:swipewear_dev@localhost:5432/swipewear",
)
IMAGE_DOWNLOAD_TIMEOUT_SECONDS = 15.0
INDEX_RESULT_SCHEMA_VERSION = 1

ImageLoader = Callable[[str], bytes]
ImageTransform = Callable[[bytes], bytes]


class EmbeddingStore(Protocol):
    """Storage operations required by the catalogue indexer."""

    def mark_stale_products(self, embedding_version: str) -> int:
        """Mark products whose stored embedding version is not current."""
        ...

    def upsert_embedding(
        self,
        product_id: str,
        embedding: np.ndarray,
        embedding_version: str,
        indexed_at: datetime,
    ) -> None:
        """Upsert one embedding and mark its product as current."""
        ...


@dataclass(frozen=True)
class IndexedProduct:
    """Versioned result for one successfully indexed product."""

    product_id: str
    embedding_version: str
    vector_dim: int
    indexed_at: datetime
    schema_version: int = INDEX_RESULT_SCHEMA_VERSION


@dataclass(frozen=True)
class BatchIndexResult:
    """Summary returned after a batch indexing run."""

    attempted: int
    indexed: int
    failed: int
    marked_for_reindex: int
    failures: dict[str, str] = field(default_factory=dict)


class PostgresEmbeddingStore:
    """pgvector-backed implementation of :class:`EmbeddingStore`."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def mark_stale_products(self, embedding_version: str) -> int:
        with self._connection:
            with self._connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE products
                       SET needs_reindex = TRUE
                     WHERE embedding_version IS DISTINCT FROM %s
                       AND needs_reindex = FALSE
                    """,
                    (embedding_version,),
                )
                return int(cursor.rowcount)

    def upsert_embedding(
        self,
        product_id: str,
        embedding: np.ndarray,
        embedding_version: str,
        indexed_at: datetime,
    ) -> None:
        vector_literal = _to_pgvector_literal(embedding)
        with self._connection:
            with self._connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO product_embeddings (
                        product_id,
                        embedding,
                        embedding_version,
                        indexed_at
                    )
                    VALUES (%s, %s::vector, %s, %s)
                    ON CONFLICT (product_id) DO UPDATE SET
                        embedding = EXCLUDED.embedding,
                        embedding_version = EXCLUDED.embedding_version,
                        indexed_at = EXCLUDED.indexed_at
                    """,
                    (
                        product_id,
                        vector_literal,
                        embedding_version,
                        indexed_at,
                    ),
                )
                cursor.execute(
                    """
                    UPDATE products
                       SET embedding_version = %s,
                           needs_reindex = FALSE
                     WHERE id = %s
                    """,
                    (embedding_version, product_id),
                )
                if cursor.rowcount != 1:
                    raise LookupError(
                        f"product {product_id!r} does not exist in products"
                    )


class CatalogueIndexer:
    """Encode primary product images and persist their vectors."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        store: EmbeddingStore,
        image_loader: ImageLoader,
        *,
        clock: Callable[[], datetime] | None = None,
        image_transform: ImageTransform | None = None,
    ) -> None:
        self._embedding_service = embedding_service
        self._store = store
        self._image_loader = image_loader
        self._image_transform = image_transform
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._version_prepared = False
        self._marked_for_reindex = 0

    def _prepare_version(self) -> None:
        if self._version_prepared:
            return
        self._marked_for_reindex = self._store.mark_stale_products(
            self._embedding_service.embedding_version
        )
        self._version_prepared = True
        if self._marked_for_reindex:
            _LOG.info(
                "Marked %d products for embedding reindex: version=%s",
                self._marked_for_reindex,
                self._embedding_service.embedding_version,
                extra={
                    "pipe_module": "embeddings.indexer",
                    "marked_for_reindex": self._marked_for_reindex,
                    "embedding_version": self._embedding_service.embedding_version,
                },
            )

    def index_product(
        self,
        record: ProductRecord,
        *,
        image: bytes | None = None,
    ) -> IndexedProduct:
        """Encode a ProductRecord's primary image and upsert its vector.

        `image` lets a caller supply bytes it already fetched, so a batch can
        download ahead of the encoder instead of serialising the two.
        """
        self._prepare_version()
        original_image = (
            image if image is not None else self._image_loader(record.image_urls[0])
        )
        image_bytes = self._transform_image(original_image, record.id)
        embedding = _validate_embedding(
            self._embedding_service.encode_image(image_bytes),
            self._embedding_service.vector_dim,
        )
        indexed_at = self._clock()
        self._store.upsert_embedding(
            record.id,
            embedding,
            self._embedding_service.embedding_version,
            indexed_at,
        )
        return IndexedProduct(
            product_id=record.id,
            embedding_version=self._embedding_service.embedding_version,
            vector_dim=self._embedding_service.vector_dim,
            indexed_at=indexed_at,
        )

    def _transform_image(self, image: bytes, product_id: str) -> bytes:
        if self._image_transform is None:
            return image
        try:
            return self._image_transform(image)
        except Exception:  # noqa: BLE001 - original-image fallback is mandatory
            _LOG.exception(
                "Image transform failed for %s; using original image",
                product_id,
                extra={
                    "pipe_module": "embeddings.indexer",
                    "product_id": product_id,
                    "fallback_used": True,
                },
            )
            return image

    def _prefetch(
        self,
        records: Sequence[ProductRecord],
        max_workers: int,
    ) -> Iterator[tuple[ProductRecord, bytes | None, Exception | None]]:
        """Yield records with their image bytes, downloading ahead of the caller.

        Measured on the real catalogue, a download costs ~520 ms against ~236 ms
        to encode: done in sequence the CPU idles two thirds of the time.

        The look-ahead is bounded rather than a plain executor.map, which would
        submit every record at once and hold the whole catalogue's images in
        memory (50 000 x ~67 KB is over 3 GB).
        """
        window = max_workers * 2
        remaining = iter(records)
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            def submit(record: ProductRecord):
                return (record, pool.submit(self._image_loader, record.image_urls[0]))

            pending = deque(
                submit(r) for r in islice(remaining, window)
            )
            while pending:
                record, future = pending.popleft()
                try:
                    yield record, future.result(), None
                except Exception as exc:  # noqa: BLE001 - reported per item below
                    yield record, None, exc
                nxt = next(remaining, None)
                if nxt is not None:
                    pending.append(submit(nxt))

    def index_batch(
        self,
        records: Sequence[ProductRecord],
        *,
        max_workers: int = 1,
    ) -> BatchIndexResult:
        """Index a batch, logging progress and continuing after item failures."""
        self._prepare_version()
        failures: dict[str, str] = {}
        indexed = 0
        total = len(records)

        if max_workers > 1:
            stream = self._prefetch(records, max_workers)
        else:
            stream = ((record, None, None) for record in records)

        for position, (record, image, download_error) in enumerate(stream, start=1):
            try:
                if download_error is not None:
                    raise download_error
                self.index_product(record, image=image)
                indexed += 1
                _LOG.info(
                    "Indexed product %d/%d: %s",
                    position,
                    total,
                    record.id,
                    extra={
                        "pipe_module": "embeddings.indexer",
                        "position": position,
                        "total": total,
                        "product_id": record.id,
                    },
                )
            except Exception as exc:  # noqa: BLE001 - one item must not stop a batch
                failures[record.id] = f"{type(exc).__name__}: {exc}"
                _LOG.exception(
                    "Failed to index product %d/%d: %s",
                    position,
                    total,
                    record.id,
                    extra={
                        "pipe_module": "embeddings.indexer",
                        "position": position,
                        "total": total,
                        "product_id": record.id,
                    },
                )

        result = BatchIndexResult(
            attempted=total,
            indexed=indexed,
            failed=len(failures),
            marked_for_reindex=self._marked_for_reindex,
            failures=failures,
        )
        _LOG.info(
            "Catalogue indexing complete: attempted=%d indexed=%d failed=%d",
            result.attempted,
            result.indexed,
            result.failed,
            extra={
                "pipe_module": "embeddings.indexer",
                "attempted": result.attempted,
                "indexed": result.indexed,
                "failed": result.failed,
            },
        )
        return result


def download_image(image_url: str) -> bytes:
    """Download an image and return its raw bytes."""
    response = requests.get(image_url, timeout=IMAGE_DOWNLOAD_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.content


def _validate_embedding(embedding: np.ndarray, vector_dim: int) -> np.ndarray:
    vector = np.asarray(embedding, dtype=np.float32)
    if vector.shape != (vector_dim,):
        raise ValueError(
            f"expected embedding shape ({vector_dim},), got {vector.shape}"
        )
    if not np.isfinite(vector).all():
        raise ValueError("embedding contains non-finite values")
    return vector


def _to_pgvector_literal(embedding: np.ndarray) -> str:
    return "[" + ",".join(str(float(value)) for value in embedding) + "]"


def _connect(database_url: str = DATABASE_URL) -> Any:
    import psycopg2  # type: ignore[import-untyped]

    return psycopg2.connect(database_url)


def _build_default_indexer(
    *,
    embedding_service: EmbeddingService | None,
    store: EmbeddingStore | None,
    image_loader: ImageLoader | None,
    image_transform: ImageTransform | None,
) -> tuple[CatalogueIndexer, Any | None]:
    if embedding_service is None:
        from embeddings.fashionsiglip import get_service

        embedding_service = get_service()
    owned_connection = None
    if store is None:
        owned_connection = _connect()
        store = PostgresEmbeddingStore(owned_connection)
    if image_transform is None:
        from vision.interfaces import get_active_image_transform

        image_transform = get_active_image_transform()
    return (
        CatalogueIndexer(
            embedding_service,
            store,
            image_loader or download_image,
            image_transform=image_transform,
        ),
        owned_connection,
    )


def index_product(
    record: ProductRecord,
    *,
    embedding_service: EmbeddingService | None = None,
    store: EmbeddingStore | None = None,
    image_loader: ImageLoader | None = None,
    image_transform: ImageTransform | None = None,
) -> IndexedProduct:
    """Index one product using production defaults unless dependencies are supplied."""
    indexer, owned_connection = _build_default_indexer(
        embedding_service=embedding_service,
        store=store,
        image_loader=image_loader,
        image_transform=image_transform,
    )
    try:
        return indexer.index_product(record)
    finally:
        if owned_connection is not None:
            owned_connection.close()


def index_batch(
    records: Sequence[ProductRecord],
    *,
    embedding_service: EmbeddingService | None = None,
    store: EmbeddingStore | None = None,
    image_loader: ImageLoader | None = None,
    image_transform: ImageTransform | None = None,
    max_workers: int = 1,
) -> BatchIndexResult:
    """Index products as one batch using production defaults or injected adapters."""
    indexer, owned_connection = _build_default_indexer(
        embedding_service=embedding_service,
        store=store,
        image_loader=image_loader,
        image_transform=image_transform,
    )
    try:
        return indexer.index_batch(records, max_workers=max_workers)
    finally:
        if owned_connection is not None:
            owned_connection.close()
