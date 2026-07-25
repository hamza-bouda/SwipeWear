"""Vector retriever -- pgvector cosine top-K (blueprint SS8).

Diagnostic: if a relevant style never enters the candidate set, check the
similarity score of the first absent product via the debug log.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Callable
from uuid import uuid4

from contracts.pipeline import CandidateItem, CandidateSet
from contracts.product import ProductCondition, ProductRecord, ProductSource
from contracts.profile import UserPreferenceProfile
from retrieval.filters import apply_hard_filters
from retrieval.watcher_filter import get_disabled_watcher_sources

_LOG = logging.getLogger("swipewear.retrieval.retriever")

# Only columns that exist in the products table (see backend/migrations/).
# ProductRecord's remaining fields (model, currency, affiliate_url,
# enriched_attrs, schema_version) carry contract defaults and are not stored.
_PRODUCT_COLUMNS = [
    "id", "source", "source_record_id", "title", "brand", "model",
    "price", "condition", "size_raw", "size_eu",
    "category", "image_urls", "available", "embedding_version",
    "listing_url",
]

# Vectors live in product_embeddings, not products — the JOIN is what makes
# the pgvector HNSW index reachable from a product query.
_QUERY_TEMPLATE = """\
SELECT {columns},
       1 - (e.embedding <=> %(style_vector)s::vector) AS similarity_score
FROM products AS p
JOIN product_embeddings AS e ON e.product_id = p.id
{where}
ORDER BY e.embedding <=> %(style_vector)s::vector
LIMIT %(k)s"""


def _to_pgvector_literal(vector: list[float]) -> str:
    """Render a Python vector as the '[a,b,c]' literal pgvector expects.

    A plain list would be adapted by psycopg2 as a Postgres ARRAY, which does
    not cast to `vector`.
    """
    return "[" + ",".join(str(float(v)) for v in vector) + "]"


class VectorRetriever:
    def __init__(self, get_conn: Callable[[], Any]) -> None:
        self._get_conn = get_conn

    def retrieve(
        self,
        profile: UserPreferenceProfile,
        k: int = 100,
    ) -> CandidateSet:
        request_id = uuid4()
        start = time.monotonic()

        # An empty positive vector is not always cold start: a profile can
        # carry events whose payload never included a product embedding.
        # Either way there is nothing to search with — let the caller fall back.
        if profile.is_cold_start or not profile.vectors.positive:
            _LOG.info(
                "No style vector available for user %s (event_count=%d)",
                profile.user_id,
                profile.event_count,
            )
            return CandidateSet(
                request_id=request_id,
                candidates=[],
                hard_filters_applied=[],
                retrieval_latency_ms=0.0,
            )

        conn = self._get_conn()
        style_vector = _to_pgvector_literal(profile.vectors.positive)
        blocked = get_disabled_watcher_sources(conn)
        filter_result = apply_hard_filters(profile, blocked_sources=blocked or None)

        query = _QUERY_TEMPLATE.format(
            columns=", ".join(f"p.{c}" for c in _PRODUCT_COLUMNS),
            where=filter_result.where_sql,
        )
        params: dict[str, object] = {
            **filter_result.params,
            "style_vector": style_vector,
            "k": k,
        }

        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

        candidates: list[CandidateItem] = []
        for rank, row in enumerate(rows, start=1):
            row_dict = dict(
                zip([*_PRODUCT_COLUMNS, "similarity_score"], row),
            )
            similarity = float(row_dict.pop("similarity_score"))
            row_dict["source"] = ProductSource(row_dict["source"])
            row_dict["condition"] = ProductCondition(row_dict["condition"])
            row_dict["price"] = float(row_dict["price"])
            row_dict["image_urls"] = list(row_dict["image_urls"] or [])
            # The column holds the raw seller URL; affiliate deep links are
            # derived from it at serve time.
            row_dict["affiliate_url"] = row_dict.pop("listing_url", None)
            product = ProductRecord(**row_dict)
            candidates.append(CandidateItem(
                product=product,
                similarity_score=similarity,
                retrieval_rank=rank,
            ))

        elapsed_ms = (time.monotonic() - start) * 1000

        if elapsed_ms > 100:
            _LOG.warning(
                "Retrieval latency %.1f ms exceeds 100 ms budget"
                " (k=%d, user=%s)",
                elapsed_ms, k, profile.user_id,
            )

        _LOG.debug(
            "Retrieved %d candidates in %.1f ms (k=%d, user=%s)",
            len(candidates), elapsed_ms, k, profile.user_id,
        )

        return CandidateSet(
            request_id=request_id,
            candidates=candidates,
            hard_filters_applied=filter_result.applied,
            retrieval_latency_ms=round(elapsed_ms, 1),
        )
