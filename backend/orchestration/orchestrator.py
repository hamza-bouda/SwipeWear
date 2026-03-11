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
from contracts.trace import RequestTrace
from orchestration.latency_budgets import annotate_budgets, severe_budget_breaches
from orchestration.interfaces import (
    ExplainerProtocol,
    PolicyProtocol,
    RankerProtocol,
    RetrieverProtocol,
)

logger = logging.getLogger("swipewear.orchestration")


def _elapsed_ms(t0: float) -> float:
    return round((time.perf_counter() - t0) * 1000, 2)


def _editable_tag_fallback(feed: RankedFeed) -> list[Explanation]:
    """Return editable tags, without a generated sentence, for each item."""
    explanations: list[Explanation] = []
    for item in feed.items:
        product = item.product
        tags = [
            value
            for value in (product.brand, product.category, product.condition.value)
            if value
        ]
        explanations.append(Explanation(
            product_id=product.id,
            editable_tags=tags,
        ))
    return explanations


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
        feed, _ = self.get_feed_with_trace(request)
        return feed

    def get_feed_with_trace(self, request: RecoRequest) -> tuple[RankedFeed, RequestTrace]:
        traces: list[ModuleTrace] = []
        profile: UserPreferenceProfile = request.user_profile
        any_fallback = False
        pipeline_started = time.perf_counter()

        # ── Step 1: hard_filter ──────────────────────────────────────────────
        # Hard constraints live in profile.hard_constraints and are forwarded
        # to the retriever as part of the RecoRequest. No separate module.
        hard_filter_started = time.perf_counter()
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
        traces.append(ModuleTrace(
            module="hard_filter", latency_ms=_elapsed_ms(hard_filter_started), version="v1",
        ))

        # ── Step 2: retrieve ─────────────────────────────────────────────────
        t0 = time.perf_counter()
        try:
            candidate_set = self._retriever.retrieve(request)
            # A retriever may degrade internally (vector KO → recent products)
            # without raising: propagate its flag or the feed would report
            # itself as healthy while carrying zero similarity signal.
            any_fallback = any_fallback or candidate_set.fallback_used
            traces.append(ModuleTrace(
                module="retrieve",
                latency_ms=_elapsed_ms(t0),
                version="v1",
                fallback_used=candidate_set.fallback_used,
            ))
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
                    module="retrieve",
                    latency_ms=elapsed,
                    version="v1",
                    fallback_used=True,
                    warnings=[warning],
                )
            )

        # ── Step 3: rank ─────────────────────────────────────────────────────
        t0 = time.perf_counter()
        try:
            ranked_feed = self._ranker.rank(candidate_set, profile)
            traces.append(ModuleTrace(module="rank", latency_ms=_elapsed_ms(t0), version="v1"))
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
                    module="rank",
                    latency_ms=elapsed,
                    version="v1",
                    fallback_used=True,
                    warnings=[warning],
                )
            )

        # ── Step 4: diversify (policy) ───────────────────────────────────────
        t0 = time.perf_counter()
        try:
            ranked_feed = self._policy.apply(ranked_feed, profile)
            traces.append(ModuleTrace(module="diversify", latency_ms=_elapsed_ms(t0), version="v1"))
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
                    module="diversify",
                    latency_ms=elapsed,
                    version="v1",
                    fallback_used=True,
                    warnings=[warning],
                )
            )

        # ── Step 5: explain ──────────────────────────────────────────────────
        t0 = time.perf_counter()
        explanations: list[Explanation] = []
        try:
            explanations = self._explainer.explain(ranked_feed, profile)
            traces.append(ModuleTrace(module="explain", latency_ms=_elapsed_ms(t0), version="v1"))
        except Exception as exc:
            # blueprint §12: explainer KO → empty list (editable_tags fallback in module)
            elapsed = _elapsed_ms(t0)
            warning = f"{type(exc).__name__}: {exc}"
            any_fallback = True
            logger.warning(
                "explainer fallback triggered",
                extra={"pipe_module": "explainability", "error": warning},
            )
            explanations = _editable_tag_fallback(ranked_feed)
            traces.append(
                ModuleTrace(
                    module="explain",
                    latency_ms=elapsed,
                    version="v1",
                    fallback_used=True,
                    warnings=[warning],
                )
            )

        if any_fallback and not ranked_feed.fallback_used:
            ranked_feed = ranked_feed.model_copy(update={"fallback_used": True})

        # Retrieval deliberately over-fetches so ranking and MMR have room to
        # choose; the caller still asked for n_results. Nothing truncated
        # before, which went unnoticed only while the pool happened to equal
        # the page size — a request for 20 was answered with 100.
        explanation_by_product = {
            explanation.product_id: explanation for explanation in explanations
        }
        ranked_feed = ranked_feed.model_copy(update={
            "items": [
                item.model_copy(update={
                    "explanation": explanation_by_product.get(item.product.id),
                })
                for item in ranked_feed.items[:request.n_results]
            ],
        })
        trace = annotate_budgets(RequestTrace(
            user_id=profile.user_id,
            modules=traces,
            total_latency_ms=_elapsed_ms(pipeline_started),
        ))
        # Keep the message itself valid JSON so standard log collectors can
        # ingest one complete trace object per recommendation request.
        logger.info("%s", trace.model_dump_json())
        for module in severe_budget_breaches(trace):
            # 'module' is a reserved LogRecord attribute: passing it in extra
            # makes logging raise KeyError, so the breach warning killed the
            # very request it was meant to flag. Every other call site in this
            # file already uses pipe_module for exactly this reason.
            logger.error(
                "latency budget severely exceeded", extra={"pipe_module": module},
            )
        return ranked_feed, trace


__all__ = ["RecoOrchestrator"]
