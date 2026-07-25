"""Guards for the four defects that made the deck stop advancing — KAN-88.

Measured before these fixes, on a stocked 50 000-product catalogue: a user who
swiped through a 15-card feed and reloaded got 13 of the same 15 cards back,
had no style vector however much they swiped, and hit an empty feed by the
third screen.
"""
from __future__ import annotations

from uuid import uuid4

from contracts.product import ProductCondition, ProductRecord, ProductSource
from contracts.profile import HardConstraints
from retrieval.filters import apply_hard_filters, matches_hard_filters


def _product(size_eu: str | None) -> ProductRecord:
    return ProductRecord(
        id="p1",
        source=ProductSource.ebay,
        source_record_id="1",
        title="Veste",
        price=50.0,
        condition=ProductCondition.good,
        category="vestes",
        image_urls=["https://example.com/i.jpg"],
        size_eu=size_eu,
    )


class _Profile:
    """Minimal stand-in: apply_hard_filters only reads hard_constraints."""

    def __init__(self, **kwargs):
        self.hard_constraints = HardConstraints(**kwargs)


class TestSeenProductsAreExcluded:
    def test_vector_query_filters_on_the_event_log(self):
        from retrieval.retriever import _QUERY_TEMPLATE

        assert "NOT EXISTS" in _QUERY_TEMPLATE
        assert "interaction_events" in _QUERY_TEMPLATE
        assert "%(user_id)s" in _QUERY_TEMPLATE

    def test_fallback_query_filters_too(self):
        """Degraded is not an excuse to re-serve what the user just swiped."""
        from retrieval.fallback import _FALLBACK_QUERY

        assert "NOT EXISTS" in _FALLBACK_QUERY
        assert "interaction_events" in _FALLBACK_QUERY

    def test_exploration_sample_filters_too(self):
        import inspect

        from api.pipeline import _random_catalogue_sample

        source = inspect.getsource(_random_catalogue_sample)
        assert "NOT EXISTS" in source
        assert "interaction_events" in source


class TestUnknownSizeIsNotAMismatch:
    """eBay item summaries almost never carry a size: 43 of 50 870 ingested
    products have one, so a strict equality filter left 15 matches."""

    def test_sql_clause_keeps_null_sizes(self):
        result = apply_hard_filters(_Profile(sizes=["M"]))
        clause = next(c for c in result.clauses if "size_eu" in c)
        assert "IS NULL" in clause

    def test_in_memory_check_keeps_an_unrecorded_size(self):
        assert matches_hard_filters(_product(None), HardConstraints(sizes=["M"]))

    def test_a_known_mismatch_is_still_excluded(self):
        assert not matches_hard_filters(
            _product("XXL"), HardConstraints(sizes=["M"]),
        )

    def test_a_match_passes(self):
        assert matches_hard_filters(_product("M"), HardConstraints(sizes=["M"]))


class TestCandidatePool:
    """Retrieving exactly n_results left MMR nothing to substitute, so a feed
    asked for 20 came back with 7 once diversification had run."""

    def test_pool_is_larger_than_the_page(self):
        from api.pipeline import RetrieverAdapter

        assert RetrieverAdapter._candidate_pool(20) > 20

    def test_pool_never_drops_below_the_blueprint_baseline(self):
        from api.pipeline import RetrieverAdapter

        assert RetrieverAdapter._candidate_pool(1) >= 100

    def test_pool_grows_with_a_large_page(self):
        from api.pipeline import RetrieverAdapter

        assert RetrieverAdapter._candidate_pool(100) >= 500


class TestFeedHonoursNResults:
    def test_orchestrator_truncates_to_the_requested_page_size(self):
        """Over-fetching for the ranker must not leak into the response: a
        request for 20 was answered with the whole 100-candidate pool."""
        from unittest.mock import MagicMock

        from contracts.pipeline import (
            CandidateItem, CandidateSet, RankedFeed, RankedItem, RecoRequest,
        )
        from contracts.profile import UserPreferenceProfile
        from orchestration.orchestrator import RecoOrchestrator

        products = [
            _product(None).model_copy(update={"id": f"p{i}"}) for i in range(60)
        ]
        request_id = uuid4()

        retriever = MagicMock()
        retriever.retrieve.return_value = CandidateSet(
            request_id=request_id,
            candidates=[
                CandidateItem(product=p, similarity_score=0.9, retrieval_rank=i)
                for i, p in enumerate(products, start=1)
            ],
            hard_filters_applied=[],
            retrieval_latency_ms=1.0,
        )
        ranker = MagicMock()
        ranker.rank.return_value = RankedFeed(
            request_id=request_id,
            items=[
                RankedItem(product=p, final_score=1.0, rank=i)
                for i, p in enumerate(products, start=1)
            ],
        )
        policy = MagicMock()
        policy.apply.side_effect = lambda feed, profile: feed
        explainer = MagicMock()
        explainer.explain.return_value = []

        orchestrator = RecoOrchestrator(
            retriever=retriever, ranker=ranker, policy=policy,
            explainer=explainer,
        )
        profile = UserPreferenceProfile(user_id=uuid4())
        feed, _ = orchestrator.get_feed_with_trace(
            RecoRequest(user_profile=profile, n_results=20),
        )
        assert len(feed.items) == 20


class TestSwipesFeedTheStyleVector:
    def test_events_router_loads_the_embedding_server_side(self):
        """preferences/updater.py reads product_embedding from the payload,
        which would require the mobile client to upload 768 floats per swipe.
        It does not, so the profile never left cold start."""
        import inspect

        from api.routers import events

        source = inspect.getsource(events)
        assert "product_embeddings" in source
        assert "product_embedding" in source
