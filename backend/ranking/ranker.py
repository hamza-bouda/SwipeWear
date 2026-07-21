"""Transparent ranker v1 — weighted feature scoring (blueprint SS11).

The ranker receives a complete profile and CandidateSet — zero DB reads.
Each feature is logged in score_breakdown for explainability.
"""
from __future__ import annotations

import logging
import math
import time
from datetime import datetime, timezone
from uuid import uuid4

from contracts.pipeline import CandidateItem, CandidateSet, RankedFeed, RankedItem
from contracts.profile import UserPreferenceProfile
from ranking.config import (
    DEFAULT_WEIGHTS,
    FRESHNESS_HALF_LIFE_DAYS,
    PRICE_FIT_THRESHOLD,
    RankingWeights,
)

_LOG = logging.getLogger("swipewear.ranking.ranker")


class TransparentRanker:
    def __init__(self, weights: RankingWeights | None = None) -> None:
        self._w = weights or DEFAULT_WEIGHTS

    def rank(
        self,
        candidates: CandidateSet,
        profile: UserPreferenceProfile,
    ) -> RankedFeed:
        request_id = candidates.request_id or uuid4()
        start = time.monotonic()

        liked_brands = {
            b.lower() for b in profile.editable_preferences.liked_brands
        }
        budget = profile.hard_constraints.max_price_eur
        now = datetime.now(timezone.utc)

        scored: list[tuple[float, dict[str, float], CandidateItem]] = []
        for ci in candidates.candidates:
            features = self._compute_features(ci, liked_brands, budget, now)
            final = (
                self._w.similarity * features["similarity"]
                + self._w.price_fit * features["price_fit"]
                + self._w.brand_boost * features["brand_boost"]
                + self._w.freshness * features["freshness"]
            )
            scored.append((final, features, ci))

        scored.sort(key=lambda t: t[0], reverse=True)

        items = [
            RankedItem(
                product=ci.product,
                final_score=round(final, 6),
                rank=rank,
                score_breakdown=features,
            )
            for rank, (final, features, ci) in enumerate(scored, start=1)
        ]

        elapsed_ms = (time.monotonic() - start) * 1000
        _LOG.info(
            "Ranked %d candidates in %.1f ms", len(items), elapsed_ms,
        )

        return RankedFeed(
            request_id=request_id,
            items=items,
            ranking_latency_ms=round(elapsed_ms, 1),
        )

    @staticmethod
    def _compute_features(
        ci: CandidateItem,
        liked_brands: set[str],
        budget: float | None,
        now: datetime,
    ) -> dict[str, float]:
        similarity = ci.similarity_score

        if budget is not None and budget > 0:
            ratio = ci.product.price / budget
            if ratio <= PRICE_FIT_THRESHOLD:
                price_fit = 1.0
            else:
                overshoot = (ratio - PRICE_FIT_THRESHOLD) / (1.0 - PRICE_FIT_THRESHOLD)
                price_fit = max(0.0, 1.0 - overshoot)
        else:
            price_fit = 0.5

        brand = ci.product.brand
        brand_boost = 1.0 if brand and brand.lower() in liked_brands else 0.0

        indexed_at_str = ci.product.enriched_attrs.get("indexed_at")
        if indexed_at_str:
            try:
                indexed_at = datetime.fromisoformat(indexed_at_str)
                if indexed_at.tzinfo is None:
                    indexed_at = indexed_at.replace(tzinfo=timezone.utc)
                age_days = (now - indexed_at).total_seconds() / 86400
                freshness = math.exp(
                    -0.693 * age_days / FRESHNESS_HALF_LIFE_DAYS
                )
            except (ValueError, TypeError):
                freshness = 0.5
        else:
            freshness = 0.5

        return {
            "similarity": round(similarity, 6),
            "price_fit": round(price_fit, 6),
            "brand_boost": round(brand_boost, 6),
            "freshness": round(freshness, 6),
        }
