from unittest.mock import MagicMock
from uuid import UUID

import pytest

from contracts.pipeline import (
    CandidateItem,
    CandidateSet,
    Explanation,
    RankedFeed,
    RankedItem,
    RecoRequest,
)
from contracts.product import ProductCondition, ProductRecord, ProductSource
from contracts.profile import UserPreferenceProfile
from orchestration.errors import (
    ExplainerError,
    PolicyError,
    RankingError,
    RetrievalError,
)
from orchestration.orchestrator import RecoOrchestrator

REQUEST_ID = UUID("00000000-0000-0000-0000-000000000099")


def _make_product(id_: str = "p-001", price: float = 50.0) -> ProductRecord:
    return ProductRecord(
        id=id_,
        source=ProductSource.ebay,
        source_record_id="src-" + id_,
        title="Test product",
        price=price,
        condition=ProductCondition.good,
        category="sneakers",
        image_urls=["https://img.test.com/1.jpg"],
        size_raw="M",
    )


def _make_candidate_set(request_id: UUID = REQUEST_ID) -> CandidateSet:
    return CandidateSet(
        request_id=request_id,
        candidates=[
            CandidateItem(
                product=_make_product("p-001", 50.0), similarity_score=0.9, retrieval_rank=1
            ),
            CandidateItem(
                product=_make_product("p-002", 40.0), similarity_score=0.7, retrieval_rank=2
            ),
        ],
    )


def _make_ranked_feed(request_id: UUID = REQUEST_ID) -> RankedFeed:
    return RankedFeed(
        request_id=request_id,
        items=[
            RankedItem(product=_make_product("p-001", 50.0), final_score=0.9, rank=1),
            RankedItem(product=_make_product("p-002", 40.0), final_score=0.7, rank=2),
        ],
    )


def _make_orchestrator(
    retriever=None, ranker=None, policy=None, explainer=None
) -> RecoOrchestrator:
    if retriever is None:
        retriever = MagicMock()
        retriever.retrieve.return_value = _make_candidate_set()
    if ranker is None:
        ranker = MagicMock()
        ranker.rank.return_value = _make_ranked_feed()
    if policy is None:
        policy = MagicMock()
        policy.apply.return_value = _make_ranked_feed()
    if explainer is None:
        explainer = MagicMock()
        explainer.explain.return_value = [Explanation(product_id="p-001")]
    return RecoOrchestrator(retriever=retriever, ranker=ranker, policy=policy, explainer=explainer)


def _make_request() -> RecoRequest:
    return RecoRequest(request_id=REQUEST_ID, user_profile=UserPreferenceProfile())


# ── Happy path ────────────────────────────────────────────────────────────────

class TestRecoOrchestratorHappyPath:
    def test_get_feed_returns_ranked_feed(self):
        orch = _make_orchestrator()
        feed = orch.get_feed(_make_request())
        assert isinstance(feed, RankedFeed)

    def test_get_feed_calls_all_modules_in_order(self):
        call_order: list[str] = []

        retriever = MagicMock()
        retriever.retrieve.side_effect = (
            lambda r: (call_order.append("retrieve"), _make_candidate_set())[1]
        )
        ranker = MagicMock()
        ranker.rank.side_effect = (
            lambda c, p: (call_order.append("rank"), _make_ranked_feed())[1]
        )
        policy = MagicMock()
        policy.apply.side_effect = (
            lambda f, p: (call_order.append("policy"), _make_ranked_feed())[1]
        )
        explainer = MagicMock()
        explainer.explain.side_effect = (
            lambda f, p: (call_order.append("explain"), [Explanation(product_id="p-001")])[1]
        )
        orch = _make_orchestrator(
            retriever=retriever, ranker=ranker, policy=policy, explainer=explainer
        )
        orch.get_feed(_make_request())
        assert call_order == ["retrieve", "rank", "policy", "explain"]

    def test_get_feed_passes_profile_to_ranker(self):
        ranker = MagicMock()
        ranker.rank.return_value = _make_ranked_feed()
        orch = _make_orchestrator(ranker=ranker)
        request = _make_request()
        orch.get_feed(request)
        ranker.rank.assert_called_once()
        _, profile_arg = ranker.rank.call_args[0]
        assert isinstance(profile_arg, UserPreferenceProfile)

    def test_get_feed_result_contains_items(self):
        orch = _make_orchestrator()
        feed = orch.get_feed(_make_request())
        assert len(feed.items) == 2
        assert feed.items[0].explanation is not None


# ── Fallbacks ────────────────────────────────────────────────────────────────

class TestRecoOrchestratorFallbacks:
    def test_retrieval_error_returns_empty_feed(self):
        retriever = MagicMock()
        retriever.retrieve.side_effect = RetrievalError("vector DB down")
        orch = _make_orchestrator(retriever=retriever)
        feed = orch.get_feed(_make_request())
        assert isinstance(feed, RankedFeed)
        assert feed.fallback_used is True

    def test_ranking_error_falls_back_to_similarity_sort(self):
        ranker = MagicMock()
        ranker.rank.side_effect = RankingError("model not loaded")
        orch = _make_orchestrator(ranker=ranker)
        feed = orch.get_feed(_make_request())
        assert isinstance(feed, RankedFeed)
        assert feed.fallback_used is True
        assert len(feed.items) == 2  # sorted from 2 candidates

    def test_policy_error_returns_untouched_feed(self):
        policy = MagicMock()
        policy.apply.side_effect = PolicyError("MMR crashed")
        orch = _make_orchestrator(policy=policy)
        feed = orch.get_feed(_make_request())
        assert isinstance(feed, RankedFeed)

    def test_explainer_error_returns_feed_without_raising(self):
        explainer = MagicMock()
        explainer.explain.side_effect = ExplainerError("LLM timeout")
        orch = _make_orchestrator(explainer=explainer)
        feed = orch.get_feed(_make_request())
        assert isinstance(feed, RankedFeed)
        assert feed.items[0].explanation is not None
        assert feed.items[0].explanation.grounded is False
        assert feed.items[0].explanation.editable_tags == ["sneakers", "good"]

    def test_generic_exception_in_retriever_is_caught(self):
        retriever = MagicMock()
        retriever.retrieve.side_effect = RuntimeError("unexpected crash")
        orch = _make_orchestrator(retriever=retriever)
        feed = orch.get_feed(_make_request())
        assert isinstance(feed, RankedFeed)

    def test_retrieval_fallback_logs_warning(self, caplog):
        import logging
        retriever = MagicMock()
        retriever.retrieve.side_effect = RetrievalError("timeout")
        orch = _make_orchestrator(retriever=retriever)
        with caplog.at_level(logging.WARNING, logger="swipewear.orchestration"):
            orch.get_feed(_make_request())
        assert any("retrieval fallback" in r.message for r in caplog.records)


# ── Errors module ─────────────────────────────────────────────────────────────

class TestErrors:
    def test_all_errors_are_orchestrator_error_subclasses(self):
        from orchestration.errors import OrchestratorError
        for cls in (RetrievalError, RankingError, PolicyError, ExplainerError):
            assert issubclass(cls, OrchestratorError)

    def test_errors_carry_message(self):
        err = RetrievalError("pgvector unreachable")
        assert "pgvector" in str(err)


class TestRequestTrace:
    def test_trace_contains_each_pipeline_stage(self):
        _, trace = _make_orchestrator().get_feed_with_trace(_make_request())

        assert [module.module for module in trace.modules] == [
            "hard_filter", "retrieve", "rank", "diversify", "explain",
        ]

    def test_ranker_failure_is_recorded_as_trace_fallback(self):
        ranker = MagicMock()
        ranker.rank.side_effect = RankingError("ranker unavailable")
        _, trace = _make_orchestrator(ranker=ranker).get_feed_with_trace(_make_request())

        rank = next(module for module in trace.modules if module.module == "rank")
        assert rank.fallback_used is True
        assert rank.warnings
