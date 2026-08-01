"""Dedicated Drop endpoint (F15).

Score = 0.5 * style_proximity + 0.3 * freshness(< 48h) + 0.2 * value_ratio
Limited to 15 items per day per user.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Response

from api.auth import get_current_user_id
from api.db import get_conn, put_conn
from api.schemas import FeedResponse
from contracts.pipeline import Explanation, RankedItem
from contracts.product import ProductCondition, ProductRecord, ProductSource
from ingestion.interfaces import ClickContext, build_affiliate_url
from preferences.interfaces import ProfileStore

_LOG = logging.getLogger("swipewear.api.drop")

router = APIRouter(prefix="/drop", tags=["drop"])

_DROP_LIMIT = 15
_FRESHNESS_WINDOW_HOURS = 48

_PRODUCT_COLUMNS = [
    "id", "source", "source_record_id", "title", "brand", "model", "gender",
    "price", "condition", "size_raw", "size_eu",
    "category", "image_urls", "available", "embedding_version",
    "listing_url",
]

_DROP_QUERY = """\
SELECT {columns},
       1 - (e.embedding <=> %(style_vector)s::vector) AS similarity,
       p.created_at AS product_created_at,
       p.price AS product_price
FROM products AS p
JOIN product_embeddings AS e ON e.product_id = p.id
{where}
  AND NOT EXISTS (
      SELECT 1 FROM interaction_events AS ie
      WHERE ie.user_id = %(user_id)s AND ie.product_id = p.id
  )
ORDER BY e.embedding <=> %(style_vector)s::vector
LIMIT %(k)s"""


def _to_pgvector_literal(vector: list[float]) -> str:
    return "[" + ",".join(str(float(v)) for v in vector) + "]"


def _freshness_score(created_at: datetime) -> float:
    now = datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    age_hours = (now - created_at).total_seconds() / 3600
    if age_hours <= _FRESHNESS_WINDOW_HOURS:
        return 1.0 - (age_hours / _FRESHNESS_WINDOW_HOURS)
    return 0.0


def _value_ratio(price: float, median_price: float) -> float:
    if median_price <= 0:
        return 0.5
    ratio = 1.0 - (price / median_price)
    return max(0.0, min(1.0, (ratio + 1.0) / 2.0))


@router.get("", response_model=FeedResponse)
def get_drop(
    response: Response = None,
    user_id: UUID = Depends(get_current_user_id),
):
    conn = None
    start = time.monotonic()
    try:
        conn = get_conn()
        profile_store = ProfileStore(lambda: conn)
        profile = profile_store.load(user_id)

        if profile.is_cold_start or not profile.vectors.positive:
            return FeedResponse(items=[], next_cursor=None, fallback_used=True)

        from retrieval.filters import apply_hard_filters
        from retrieval.watcher_filter import get_disabled_watcher_sources

        style_vector = _to_pgvector_literal(profile.vectors.positive)
        blocked = get_disabled_watcher_sources(conn)
        filter_result = apply_hard_filters(profile, blocked_sources=blocked or None)

        query = _DROP_QUERY.format(
            columns=", ".join(f"p.{c}" for c in _PRODUCT_COLUMNS),
            where=filter_result.where_sql,
        )
        params = {
            **filter_result.params,
            "style_vector": style_vector,
            "user_id": str(user_id),
            "k": 100,
        }

        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

        if not rows:
            return FeedResponse(items=[], next_cursor=None, fallback_used=True)

        prices = [float(r[_PRODUCT_COLUMNS.index("price")]) for r in rows]
        median_price = sorted(prices)[len(prices) // 2] if prices else 50.0

        scored: list[tuple[float, dict, float]] = []
        for row in rows:
            row_dict = dict(zip(
                [*_PRODUCT_COLUMNS, "similarity", "product_created_at", "product_price"],
                row,
            ))
            similarity = float(row_dict.pop("similarity"))
            created_at = row_dict.pop("product_created_at")
            _ = row_dict.pop("product_price")

            freshness = _freshness_score(created_at)
            value = _value_ratio(float(row_dict["price"]), median_price)
            drop_score = 0.5 * similarity + 0.3 * freshness + 0.2 * value

            scored.append((drop_score, row_dict, similarity))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:_DROP_LIMIT]

        items: list[RankedItem] = []
        for rank, (drop_score, row_dict, similarity) in enumerate(top, start=1):
            row_dict["source"] = ProductSource(row_dict["source"])
            row_dict["condition"] = ProductCondition(row_dict["condition"])
            row_dict["price"] = float(row_dict["price"])
            row_dict["image_urls"] = list(row_dict["image_urls"] or [])
            row_dict["affiliate_url"] = row_dict.pop("listing_url", None)
            product = ProductRecord(**row_dict)

            url = build_affiliate_url(product, ClickContext.feed)
            if url and url != (product.affiliate_url or ""):
                product = product.model_copy(update={"affiliate_url": url})

            items.append(RankedItem(
                product=product,
                final_score=round(drop_score, 4),
                rank=rank,
                explanation=Explanation(
                    product_id=product.id,
                    editable_tags=[
                        v for v in (product.brand, product.category)
                        if v
                    ],
                ),
            ))

        elapsed_ms = (time.monotonic() - start) * 1000
        _LOG.info("Drop for user %s: %d items in %.0f ms", user_id, len(items), elapsed_ms)

        return FeedResponse(items=items, next_cursor=None, fallback_used=False)

    except Exception:
        _LOG.error("Drop failed for user %s", user_id, exc_info=True)
        return FeedResponse(items=[], next_cursor=None, fallback_used=True)

    finally:
        if conn is not None:
            put_conn(conn)
