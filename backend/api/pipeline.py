"""Adapters that wire real modules to the orchestrator's protocols."""
from __future__ import annotations

import logging
from typing import Any, Callable

from contracts.pipeline import (
    CandidateSet,
    Explanation,
    RankedFeed,
    RecoRequest,
)
from contracts.product import ProductCondition, ProductRecord, ProductSource
from contracts.profile import UserPreferenceProfile
from explainability.explainer import GroundedExplainer, fallback_explanation
from orchestration.orchestrator import RecoOrchestrator
from policy.interfaces import epsilon_greedy_inject, mmr_rerank
from ranking.interfaces import TransparentRanker
from retrieval.interfaces import FallbackRetriever, VectorRetriever

_LOG = logging.getLogger("swipewear.api.pipeline")

_SAMPLE_COLUMNS = [
    "id", "source", "source_record_id", "title", "price",
    "condition", "category", "image_urls", "size_raw", "size_eu",
    "brand", "embedding_version",
]


def _random_catalogue_sample(
    get_conn: Callable[[], Any], n: int = 20,
) -> list[ProductRecord]:
    """Fetch a random product sample for epsilon-greedy exploration (blueprint §8)."""
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT {', '.join(_SAMPLE_COLUMNS)} FROM products"
                " WHERE available = true ORDER BY RANDOM() LIMIT %s",
                (n,),
            )
            rows = cur.fetchall()
        products = []
        for row in rows:
            d = dict(zip(_SAMPLE_COLUMNS, row))
            d["source"] = ProductSource(d["source"])
            d["condition"] = ProductCondition(d["condition"])
            d["price"] = float(d["price"])
            d["image_urls"] = list(d["image_urls"] or [])
            products.append(ProductRecord(**d))
        return products
    except Exception:
        _LOG.warning("Exploration sample fetch failed — skipping inject", exc_info=True)
        return []


class RetrieverAdapter:
    """Adapts VectorRetriever (profile, k) to RetrieverProtocol (request)."""

    def __init__(self, get_conn: Callable[[], Any]) -> None:
        self._vector = VectorRetriever(get_conn)
        self._fallback = FallbackRetriever(get_conn)

    def retrieve(self, request: RecoRequest) -> CandidateSet:
        try:
            result = self._vector.retrieve(
                request.user_profile, k=request.n_results,
            )
            if not result.candidates:
                _LOG.info("Vector retriever returned 0 candidates, trying fallback")
                return self._fallback.retrieve(
                    request.user_profile, k=request.n_results,
                )
            return result
        except Exception:
            _LOG.warning("Vector retriever failed, using fallback", exc_info=True)
            return self._fallback.retrieve(
                request.user_profile, k=request.n_results,
            )


class PolicyAdapter:
    """MMR diversity + epsilon-greedy exploration (blueprint §8)."""

    def __init__(self, get_conn: Callable[[], Any]) -> None:
        self._get_conn = get_conn

    def apply(
        self, feed: RankedFeed, profile: UserPreferenceProfile,
    ) -> RankedFeed:
        feed = mmr_rerank(feed)
        sample = _random_catalogue_sample(self._get_conn)
        return epsilon_greedy_inject(feed, sample)


class FallbackExplainer:
    """Blueprint SS12: explainer KO -> editable tags, no sentence."""

    def explain(
        self, feed: RankedFeed, profile: UserPreferenceProfile,
    ) -> list[Explanation]:
        explanations: list[Explanation] = []
        for item in feed.items:
            explanations.append(fallback_explanation(item))
        return explanations


def build_orchestrator(get_conn: Callable[[], Any]) -> RecoOrchestrator:
    return RecoOrchestrator(
        retriever=RetrieverAdapter(get_conn),
        ranker=TransparentRanker(),
        policy=PolicyAdapter(get_conn),
        explainer=GroundedExplainer(),
    )
