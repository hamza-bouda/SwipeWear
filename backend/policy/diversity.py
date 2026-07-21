"""MMR diversity reranking — no quasi-duplicates in the feed (blueprint SS8)."""
from __future__ import annotations

import logging
import math
import time

from contracts.pipeline import RankedFeed, RankedItem

_LOG = logging.getLogger("swipewear.policy.diversity")


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a < 1e-9 or norm_b < 1e-9:
        return 0.0
    return dot / (norm_a * norm_b)


def _category_similarity(item_a: RankedItem, item_b: RankedItem) -> float:
    if item_a.product.category == item_b.product.category:
        brand_a = (item_a.product.brand or "").lower()
        brand_b = (item_b.product.brand or "").lower()
        if brand_a and brand_a == brand_b:
            return 0.9
        return 0.7
    return 0.0


def mmr_rerank(
    ranked_feed: RankedFeed,
    embeddings: dict[str, list[float]] | None = None,
    lambda_: float = 0.7,
) -> RankedFeed:
    start = time.monotonic()
    items = list(ranked_feed.items)

    if len(items) <= 1:
        return ranked_feed.model_copy(update={"diversity_applied": True})

    max_score = max(it.final_score for it in items) or 1.0

    selected: list[RankedItem] = []
    remaining = list(items)

    while remaining:
        best_idx = 0
        best_mmr = -float("inf")

        for i, candidate in enumerate(remaining):
            relevance = candidate.final_score / max_score

            if not selected:
                max_sim = 0.0
            else:
                max_sim = max(
                    _item_similarity(candidate, sel, embeddings)
                    for sel in selected
                )

            mmr = lambda_ * relevance - (1 - lambda_) * max_sim

            if mmr > best_mmr:
                best_mmr = mmr
                best_idx = i

        selected.append(remaining.pop(best_idx))

    reranked = [
        item.model_copy(update={"rank": rank})
        for rank, item in enumerate(selected, start=1)
    ]

    elapsed_ms = (time.monotonic() - start) * 1000
    _LOG.info("MMR reranked %d items in %.1f ms", len(reranked), elapsed_ms)

    return ranked_feed.model_copy(
        update={
            "items": reranked,
            "diversity_applied": True,
        },
    )


def _item_similarity(
    a: RankedItem,
    b: RankedItem,
    embeddings: dict[str, list[float]] | None,
) -> float:
    if embeddings:
        emb_a = embeddings.get(a.product.id)
        emb_b = embeddings.get(b.product.id)
        if emb_a and emb_b:
            return _cosine_similarity(emb_a, emb_b)
    return _category_similarity(a, b)
