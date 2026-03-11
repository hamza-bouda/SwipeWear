"""Price ladder builder — multi-source aggregation for a liked product.

Given a product_id, finds comparable offers across all sources (used + new)
via FashionSigLIP vector similarity, refined by GLiNER brand/model match.
Results sorted by price ascending. Budget: < 800 ms total.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Callable

from contracts.pipeline import (
    MatchConfidence,
    PriceLadder,
    PriceLadderEntry,
)
from contracts.product import ProductCondition, ProductRecord, ProductSource

_LOG = logging.getLogger("swipewear.retrieval.ladder")

DEFAULT_MIN_SIMILARITY = float(os.getenv("LADDER_MIN_SIMILARITY", "0.70"))
DEFAULT_MAX_RESULTS = 15
LATENCY_BUDGET_MS = 800

# Only columns that exist in the products table (see backend/migrations/).
# ProductRecord's remaining fields (model, currency, enriched_attrs,
# schema_version) carry contract defaults and are not stored.
_PRODUCT_COLUMNS = [
    "id", "source", "source_record_id", "title", "brand", "model", "gender",
    "price", "condition", "size_raw", "size_eu",
    "category", "image_urls", "available", "embedding_version",
    "listing_url",
]

_FETCH_EMBEDDING_SQL = """\
SELECT embedding FROM product_embeddings WHERE product_id = %(product_id)s LIMIT 1"""

_FETCH_PRODUCT_SQL = """\
SELECT {columns} FROM products AS p WHERE p.id = %(product_id)s LIMIT 1"""

# Vectors live in product_embeddings, not products — the JOIN is what makes
# the pgvector HNSW index reachable from a product query.
_LADDER_QUERY = """\
SELECT {columns},
       1 - (e.embedding <=> %(style_vector)s::vector) AS similarity_score
FROM products AS p
JOIN product_embeddings AS e ON e.product_id = p.id
WHERE p.available = true
  AND p.id != %(source_id)s
  AND 1 - (e.embedding <=> %(style_vector)s::vector) >= %(min_similarity)s
ORDER BY e.embedding <=> %(style_vector)s::vector
LIMIT %(k)s"""


def _row_to_product(row: tuple, columns: list[str]) -> ProductRecord:
    row_dict = dict(zip(columns, row))
    row_dict["source"] = ProductSource(row_dict["source"])
    row_dict["condition"] = ProductCondition(row_dict["condition"])
    # The column holds the raw seller URL; affiliate deep links are derived
    # from it at serve time, so the contract field is filled from it here.
    row_dict["affiliate_url"] = row_dict.pop("listing_url", None)
    row_dict["price"] = float(row_dict["price"])
    row_dict["image_urls"] = list(row_dict["image_urls"] or [])
    return ProductRecord(**row_dict)


def _compute_confidence(
    source_product: ProductRecord,
    candidate: ProductRecord,
) -> MatchConfidence:
    src_brand = (source_product.brand or "").strip().lower()
    src_model = (source_product.model or "").strip().lower()
    cand_brand = (candidate.brand or "").strip().lower()
    cand_model = (candidate.model or "").strip().lower()

    if src_brand and cand_brand and src_brand == cand_brand:
        if src_model and cand_model and src_model == cand_model:
            return MatchConfidence.exact
    return MatchConfidence.similar


def build_price_ladder(
    product_id: str,
    get_conn: Callable[[], Any],
    *,
    max_results: int = DEFAULT_MAX_RESULTS,
    min_similarity: float = DEFAULT_MIN_SIMILARITY,
) -> PriceLadder:
    start = time.monotonic()
    conn = get_conn()

    with conn.cursor() as cur:
        cur.execute(_FETCH_PRODUCT_SQL.format(
            columns=", ".join(f"p.{c}" for c in _PRODUCT_COLUMNS),
        ), {"product_id": product_id})
        source_row = cur.fetchone()

    if source_row is None:
        _LOG.warning("Product %s not found for price ladder", product_id)
        elapsed = (time.monotonic() - start) * 1000
        return PriceLadder(
            source_product_id=product_id,
            latency_ms=round(elapsed, 1),
        )

    source_product = _row_to_product(source_row, _PRODUCT_COLUMNS)

    with conn.cursor() as cur:
        cur.execute(_FETCH_EMBEDDING_SQL, {"product_id": product_id})
        emb_row = cur.fetchone()

    if emb_row is None or emb_row[0] is None:
        _LOG.warning("No embedding for product %s", product_id)
        elapsed = (time.monotonic() - start) * 1000
        return PriceLadder(
            source_product_id=product_id,
            latency_ms=round(elapsed, 1),
        )

    style_vector = emb_row[0]

    with conn.cursor() as cur:
        cur.execute(
            _LADDER_QUERY.format(
                columns=", ".join(f"p.{c}" for c in _PRODUCT_COLUMNS)
            ),
            {
                "style_vector": style_vector,
                "source_id": product_id,
                "min_similarity": min_similarity,
                "k": max_results * 3,
            },
        )
        rows = cur.fetchall()

    entries: list[PriceLadderEntry] = []
    for row in rows:
        col_values = row[:len(_PRODUCT_COLUMNS)]
        similarity = float(row[len(_PRODUCT_COLUMNS)])
        candidate = _row_to_product(col_values, _PRODUCT_COLUMNS)

        confidence = _compute_confidence(source_product, candidate)

        entries.append(PriceLadderEntry(
            product_id=candidate.id,
            url=candidate.affiliate_url or "",
            price_eur=candidate.price,
            source=candidate.source.value,
            condition=candidate.condition.value,
            is_new=candidate.condition == ProductCondition.new,
            affiliate_url=candidate.affiliate_url,
            confidence=confidence,
            similarity_score=round(similarity, 3),
            image_url=candidate.image_urls[0] if candidate.image_urls else None,
            title=candidate.title,
        ))

    entries.sort(
        key=lambda e: (
            0 if e.confidence == MatchConfidence.exact else 1,
            e.price_eur,
        ),
    )
    entries = entries[:max_results]

    entries.sort(key=lambda e: e.price_eur)

    elapsed_ms = (time.monotonic() - start) * 1000

    if elapsed_ms > LATENCY_BUDGET_MS:
        _LOG.warning(
            "Price ladder latency %.1f ms exceeds %d ms budget",
            elapsed_ms, LATENCY_BUDGET_MS,
        )

    prices = [e.price_eur for e in entries]
    min_price = min(prices) if prices else None
    max_price = max(prices) if prices else None
    savings_pct = None
    if min_price is not None and max_price is not None and max_price > 0:
        savings_pct = round((1 - min_price / max_price) * 100, 1)

    _LOG.debug(
        "Price ladder for %s: %d entries in %.1f ms",
        product_id, len(entries), elapsed_ms,
    )

    return PriceLadder(
        source_product_id=product_id,
        entries=entries,
        min_price_eur=min_price,
        max_price_eur=max_price,
        savings_pct=savings_pct,
        latency_ms=round(elapsed_ms, 1),
    )
