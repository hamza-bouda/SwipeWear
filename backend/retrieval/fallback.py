"""Fallback retriever -- recent products respecting hard constraints.

Used when the vector retriever fails (pgvector down, index corrupt).
Never an empty feed -- blueprint SS12.
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
from retrieval.retriever import VectorRetriever

_LOG = logging.getLogger("swipewear.retrieval.fallback")

_DB_COLUMNS = [
    "id", "source", "source_record_id", "title", "price",
    "condition", "category", "image_urls", "size_raw", "size_eu",
    "brand", "embedding_version",
]

_FALLBACK_QUERY = """\
SELECT {columns}
FROM products
{where}
ORDER BY created_at DESC
LIMIT %(k)s"""


class FallbackRetriever:
    def __init__(self, get_conn: Callable[[], Any]) -> None:
        self._get_conn = get_conn

    def retrieve(
        self,
        profile: UserPreferenceProfile,
        k: int = 100,
    ) -> CandidateSet:
        request_id = uuid4()
        start = time.monotonic()

        _LOG.warning(
            "Fallback retriever activated for user %s", profile.user_id,
        )

        filter_result = apply_hard_filters(profile)
        query = _FALLBACK_QUERY.format(
            columns=", ".join(_DB_COLUMNS),
            where=filter_result.where_sql,
        )
        params: dict[str, object] = {**filter_result.params, "k": k}

        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

        candidates: list[CandidateItem] = []
        for rank, row in enumerate(rows, start=1):
            row_dict = dict(zip(_DB_COLUMNS, row))
            row_dict["source"] = ProductSource(row_dict["source"])
            row_dict["condition"] = ProductCondition(row_dict["condition"])
            row_dict["price"] = float(row_dict["price"])
            row_dict["image_urls"] = list(row_dict["image_urls"] or [])
            product = ProductRecord(**row_dict)
            candidates.append(CandidateItem(
                product=product,
                similarity_score=0.0,
                retrieval_rank=rank,
            ))

        elapsed_ms = (time.monotonic() - start) * 1000
        return CandidateSet(
            request_id=request_id,
            candidates=candidates,
            hard_filters_applied=filter_result.applied,
            retrieval_latency_ms=round(elapsed_ms, 1),
            fallback_used=True,
        )


def retrieve_with_fallback(
    vector_retriever: VectorRetriever,
    fallback_retriever: FallbackRetriever,
    profile: UserPreferenceProfile,
    k: int = 100,
) -> CandidateSet:
    try:
        return vector_retriever.retrieve(profile, k=k)
    except Exception:
        _LOG.exception(
            "VectorRetriever failed for user %s, using fallback",
            profile.user_id,
        )
        return fallback_retriever.retrieve(profile, k=k)
