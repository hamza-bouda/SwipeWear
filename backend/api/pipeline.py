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
from contracts.profile import UserPreferenceProfile
from explainability.explainer import GroundedExplainer, fallback_explanation
from orchestration.orchestrator import RecoOrchestrator
from policy.interfaces import mmr_rerank
from ranking.interfaces import TransparentRanker
from retrieval.interfaces import FallbackRetriever, VectorRetriever

_LOG = logging.getLogger("swipewear.api.pipeline")


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
            if not result.candidates and not request.user_profile.is_cold_start:
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
    """Adapts mmr_rerank(feed) to PolicyProtocol.apply(feed, profile)."""

    def apply(
        self, feed: RankedFeed, profile: UserPreferenceProfile,
    ) -> RankedFeed:
        return mmr_rerank(feed)


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
        policy=PolicyAdapter(),
        explainer=GroundedExplainer(),
    )
