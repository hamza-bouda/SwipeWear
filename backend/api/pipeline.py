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
from retrieval.filters import apply_hard_filters
from retrieval.interfaces import FallbackRetriever, VectorRetriever

_LOG = logging.getLogger("swipewear.api.pipeline")

_SAMPLE_COLUMNS = [
    "id", "source", "source_record_id", "title", "price",
    "condition", "category", "image_urls", "size_raw", "size_eu",
    "brand", "model", "gender", "embedding_version", "listing_url",
]


def _random_catalogue_sample(
    get_conn: Callable[[], Any],
    profile: UserPreferenceProfile,
    n: int = 20,
) -> list[ProductRecord]:
    """Fetch a random product sample for epsilon-greedy exploration (blueprint §8).

    Exploration means showing something the ranker would not have picked — not
    something the user has already swiped away, and not something they told us
    they cannot wear. This query used to filter on availability alone, so it
    bypassed every hard constraint the retriever had just applied: measured on
    a men's profile, the sample put one women's product back into the feed.
    Exploration varies style; it does not override a hard filter.
    """
    try:
        conn = get_conn()
        filter_result = apply_hard_filters(profile)
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT {', '.join('p.' + c for c in _SAMPLE_COLUMNS)}"
                " FROM products AS p"
                f" {filter_result.where_sql}"
                "   AND NOT EXISTS ("
                "     SELECT 1 FROM interaction_events AS ie"
                "     WHERE ie.user_id = %(user_id)s AND ie.product_id = p.id)"
                " ORDER BY RANDOM() LIMIT %(n)s",
                {
                    **filter_result.params,
                    "user_id": str(profile.user_id),
                    "n": n,
                },
            )
            rows = cur.fetchall()
        products = []
        for row in rows:
            d = dict(zip(_SAMPLE_COLUMNS, row))
            d["source"] = ProductSource(d["source"])
            d["condition"] = ProductCondition(d["condition"])
            d["price"] = float(d["price"])
            d["image_urls"] = list(d["image_urls"] or [])
            # The column holds the raw seller URL; affiliate deep links are
            # derived from it at serve time.
            d["affiliate_url"] = d.pop("listing_url", None)
            products.append(ProductRecord(**d))
        return products
    except Exception:
        _LOG.warning("Exploration sample fetch failed — skipping inject", exc_info=True)
        try:
            get_conn().rollback()
        except Exception:  # noqa: BLE001 - never mask the original failure
            pass
        return []


class RetrieverAdapter:
    """Adapts VectorRetriever (profile, k) to RetrieverProtocol (request)."""

    def __init__(self, get_conn: Callable[[], Any]) -> None:
        self._get_conn = get_conn
        self._vector = VectorRetriever(get_conn)
        self._fallback = FallbackRetriever(get_conn)

    def _rollback(self) -> None:
        """Clear an aborted transaction so the fallback query can still run.

        A failed statement leaves psycopg2 in InFailedSqlTransaction: without
        this, the fallback fails too and the feed comes back empty instead of
        degraded (blueprint §12).
        """
        try:
            self._get_conn().rollback()
        except Exception:  # noqa: BLE001 - rollback must never mask the real error
            _LOG.warning("Rollback failed before fallback retrieval", exc_info=True)

    @staticmethod
    def _candidate_pool(n_results: int) -> int:
        """How many candidates to retrieve to return n_results.

        Retrieving exactly n_results left ranking and MMR nothing to choose
        from — they could only drop items, never substitute — so a feed asked
        for 20 came back with 7 once diversification had done its work. The
        blueprint sizes retrieval at ~100 candidates for a 30-item feed
        (§9: retrieve 100 ms), which is what this restores.
        """
        return max(100, n_results * 5)

    def retrieve(self, request: RecoRequest) -> CandidateSet:
        k = self._candidate_pool(request.n_results)
        try:
            result = self._vector.retrieve(request.user_profile, k=k)
            if not result.candidates:
                _LOG.info("Vector retriever returned 0 candidates, trying fallback")
                return self._fallback.retrieve(request.user_profile, k=k)
            return result
        except Exception:
            _LOG.warning("Vector retriever failed, using fallback", exc_info=True)
            self._rollback()
            return self._fallback.retrieve(request.user_profile, k=k)


class PolicyAdapter:
    """MMR diversity + epsilon-greedy exploration (blueprint §8)."""

    def __init__(self, get_conn: Callable[[], Any]) -> None:
        self._get_conn = get_conn

    def apply(
        self, feed: RankedFeed, profile: UserPreferenceProfile,
    ) -> RankedFeed:
        feed = mmr_rerank(feed)
        sample = _random_catalogue_sample(self._get_conn, profile)
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
