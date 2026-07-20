from __future__ import annotations

import logging
import time

from contracts.pipeline import (
    CandidateSet,
    Explanation,
    ModuleTrace,
    RankedFeed,
    RecoRequest,
)
from contracts.profile import UserPreferenceProfile
from orchestration.interfaces import (
    ExplainerProtocol,
    PolicyProtocol,
    RankerProtocol,
    RetrieverProtocol,
)

logger = logging.getLogger("swipewear.orchestration")


def _elapsed_ms(t0: float) -> float:
    return round((time.perf_counter() - t0) * 1000, 2)


class RecoOrchestrator:
    """Sequences pipeline calls. Contains NO business logic — only call ordering.

    Module responsibilities (blueprint §11):
      hard_filter → retriever → ranker → policy → explainer
    Fallback rules (blueprint §12):
      retriever KO  → empty CandidateSet (fallback_used=True)
      ranker KO     → candidates sorted by similarity_score (fallback_used=True)
      policy KO     → ranked feed untouched (fallback_used=True)
      explainer KO  → empty explanations, editable_tags handled in module
    """

    def __init__(
        self,
        retriever: RetrieverProtocol,
        ranker: RankerProtocol,
        policy: PolicyProtocol,
        explainer: ExplainerProtocol,
    ) -> None:
        self._retriever = retriever
        self._ranker = ranker
        self._policy = policy
        self._explainer = explainer

    def get_feed(self, request: RecoRequest) -> RankedFeed:
        traces: list[ModuleTrace] = []
        profile: UserPreferenceProfile = request.user_profile
        any_fallback = False

        # ── Step 1: hard_filter ──────────────────────────────────────────────
        # Hard constraints live in profile.hard_constraints and are forwarded
        # to the retriever as part of the RecoRequest. No separate module.
        hard_filters = [
            *(f"size:{s}" for s in profile.hard_constraints.sizes),
            *(f"excl_condition:{c}" for c in profile.hard_constraints.excluded_conditions),
            *(
                [f"max_price:{profile.hard_constraints.max_price_eur}"]
                if profile.hard_constraints.max_price_eur is not None
                else []
            ),
        ]
        logger.debug(
            "hard_filter applied",
            extra={"pipe_module": "hard_filter", "filters": hard_filters},
        )

        # ── Step 2: retrieve ─────────────────────────────────────────────────
        t0 = time.perf_counter()
        try:
            candidate_set = self._retriever.retrieve(request)
            traces.append(ModuleTrace(module="retrieval", latency_ms=_elapsed_ms(t0)))
        except Exception as exc:
            # blueprint §12: retriever KO → empty set flagged as fallback
            elapsed = _elapsed_ms(t0)
            warning = f"{type(exc).__name__}: {exc}"
            logger.warning(
                "retrieval fallback triggered",
                extra={"pipe_module": "retrieval", "error": warning},
            )
            any_fallback = True
            candidate_set = CandidateSet(
                request_id=request.request_id,
                candidates=[],
                hard_filters_applied=hard_filters,
                fallback_used=True,
            )
            traces.append(
                ModuleTrace(
                    module="retrieval",
                    latency_ms=elapsed,
                    fallback_used=True,
                    warnings=[warning],
                )
            )

        # ── Step 3: rank ─────────────────────────────────────────────────────
        t0 = time.perf_counter()
        try:
            ranked_feed = self._ranker.rank(candidate_set, profile)
            traces.append(ModuleTrace(module="ranking", latency_ms=_elapsed_ms(t0)))
        except Exception as exc:
            # blueprint §12: ranker KO → candidates sorted by similarity_score
            elapsed = _elapsed_ms(t0)
            warning = f"{type(exc).__name__}: {exc}"
            logger.warning(
                "ranking fallback triggered",
                extra={"pipe_module": "ranking", "error": warning},
            )
            from contracts.pipeline import RankedItem

            fallback_items = [
                RankedItem(
                    product=c.product,
                    final_score=c.similarity_score,
                    rank=i + 1,
                )
                for i, c in enumerate(
                    sorted(
                        candidate_set.candidates,
                        key=lambda c: c.similarity_score,
                        reverse=True,
                    )
                )
            ]
            any_fallback = True
            ranked_feed = RankedFeed(
                request_id=request.request_id,
                items=fallback_items,
                fallback_used=True,
            )
            traces.append(
                ModuleTrace(
                    module="ranking",
                    latency_ms=elapsed,
                    fallback_used=True,
                    warnings=[warning],
                )
            )

        # ── Step 4: diversify (policy) ───────────────────────────────────────
        t0 = time.perf_counter()
        try:
            ranked_feed = self._policy.apply(ranked_feed, profile)
            traces.append(ModuleTrace(module="policy", latency_ms=_elapsed_ms(t0)))
        except Exception as exc:
            # blueprint §12: policy KO → ranked feed untouched
            elapsed = _elapsed_ms(t0)
            warning = f"{type(exc).__name__}: {exc}"
            any_fallback = True
            logger.warning(
                "policy fallback triggered",
                extra={"pipe_module": "policy", "error": warning},
            )
            traces.append(
                ModuleTrace(
                    module="policy",
                    latency_ms=elapsed,
                    fallback_used=True,
                    warnings=[warning],
                )
            )

        # ── Step 5: explain ──────────────────────────────────────────────────
        t0 = time.perf_counter()
        explanations: list[Explanation] = []
        try:
            explanations = self._explainer.explain(ranked_feed, profile)
            traces.append(ModuleTrace(module="explainability", latency_ms=_elapsed_ms(t0)))
        except Exception as exc:
            # blueprint §12: explainer KO → empty list (editable_tags fallback in module)
            elapsed = _elapsed_ms(t0)
            warning = f"{type(exc).__name__}: {exc}"
            any_fallback = True
            logger.warning(
                "explainer fallback triggered",
                extra={"pipe_module": "explainability", "error": warning},
            )
            traces.append(
                ModuleTrace(
                    module="explainability",
                    latency_ms=elapsed,
                    fallback_used=True,
                    warnings=[warning],
                )
            )

        if any_fallback and not ranked_feed.fallback_used:
            ranked_feed = ranked_feed.model_copy(update={"fallback_used": True})

        logger.info(
            "pipeline complete",
            extra={
                "request_id": str(request.request_id),
                "n_candidates": len(candidate_set.candidates),
                "n_results": len(ranked_feed.items),
                "n_explanations": len(explanations),
                "traces": [t.model_dump() for t in traces],
            },
        )
        return ranked_feed


__all__ = ["RecoOrchestrator"]
