from uuid import UUID

import pytest

from contracts.pipeline import (
    CandidateItem,
    CandidateSet,
    Explanation,
    ModuleTrace,
    PriceLadderEntry,
    RankedFeed,
    RankedItem,
    RecoRequest,
)
from contracts.product import ProductCondition, ProductRecord, ProductSource
from contracts.profile import UserPreferenceProfile


def make_product(**kwargs) -> ProductRecord:
    defaults = {
        "id": "prod-001",
        "source": ProductSource.ebay,
        "source_record_id": "ebay-123",
        "title": "Nike Air Max 90",
        "price": 79.99,
        "condition": ProductCondition.good,
        "category": "sneakers",
        "image_urls": ["https://img.example.com/1.jpg"],
    }
    return ProductRecord(**{**defaults, **kwargs})


PRODUCT = make_product()


class TestRecoRequest:
    def test_minimal_instantiation(self):
        profile = UserPreferenceProfile()
        req = RecoRequest(user_profile=profile)
        assert isinstance(req.request_id, UUID)
        assert req.n_results == 30
        assert req.session_intent is None
        assert req.schema_version == 1

    def test_with_session_intent(self):
        req = RecoRequest(
            user_profile=UserPreferenceProfile(),
            n_results=20,
            session_intent="sport",
        )
        assert req.session_intent == "sport"
        assert req.n_results == 20

    def test_serialization_roundtrip(self):
        req = RecoRequest(user_profile=UserPreferenceProfile())
        restored = RecoRequest.model_validate_json(req.model_dump_json())
        assert restored.request_id == req.request_id


class TestCandidateSet:
    def test_minimal_instantiation(self):
        candidate = CandidateItem(
            product=PRODUCT,
            similarity_score=0.92,
            retrieval_rank=1,
        )
        cs = CandidateSet(
            request_id=UUID("00000000-0000-0000-0000-000000000001"),
            candidates=[candidate],
        )
        assert len(cs.candidates) == 1
        assert cs.fallback_used is False
        assert cs.hard_filters_applied == []
        assert cs.schema_version == 1

    def test_with_hard_filters(self):
        cs = CandidateSet(
            request_id=UUID("00000000-0000-0000-0000-000000000002"),
            candidates=[],
            hard_filters_applied=["size:M", "max_price:120"],
            retrieval_latency_ms=87.3,
        )
        assert "size:M" in cs.hard_filters_applied
        assert cs.retrieval_latency_ms == 87.3

    def test_serialization_roundtrip(self):
        cs = CandidateSet(
            request_id=UUID("00000000-0000-0000-0000-000000000003"),
            candidates=[CandidateItem(product=PRODUCT, similarity_score=0.8, retrieval_rank=1)],
        )
        restored = CandidateSet.model_validate_json(cs.model_dump_json())
        assert restored == cs


class TestRankedFeed:
    def test_minimal_instantiation(self):
        item = RankedItem(product=PRODUCT, final_score=0.88, rank=1)
        feed = RankedFeed(
            request_id=UUID("00000000-0000-0000-0000-000000000004"),
            items=[item],
        )
        assert feed.diversity_applied is False
        assert feed.fallback_used is False
        assert feed.schema_version == 1

    def test_ranked_item_with_score_breakdown(self):
        item = RankedItem(
            product=PRODUCT,
            final_score=0.75,
            rank=1,
            score_breakdown={"similarity": 0.9, "price_fit": 0.6},
        )
        assert item.score_breakdown["similarity"] == 0.9

    def test_price_ladder_entry(self):
        entry = PriceLadderEntry(
            url="https://ebay.com/item/123",
            price_eur=79.99,
            source="ebay",
            is_new=False,
            affiliate_url="https://rover.ebay.com/...",
        )
        assert entry.price_eur == 79.99
        assert entry.is_new is False

    def test_serialization_roundtrip(self):
        feed = RankedFeed(
            request_id=UUID("00000000-0000-0000-0000-000000000005"),
            items=[RankedItem(product=PRODUCT, final_score=0.9, rank=1)],
            diversity_applied=True,
        )
        restored = RankedFeed.model_validate_json(feed.model_dump_json())
        assert restored == feed


class TestExplanation:
    def test_minimal_instantiation(self):
        expl = Explanation(product_id="prod-001")
        assert expl.grounded is False
        assert expl.reasons == []
        assert expl.evidence_refs == []
        assert expl.sentence is None
        assert expl.schema_version == 1

    def test_full_explanation(self):
        expl = Explanation(
            product_id="prod-001",
            reasons=["Corresponds à tes marques aimées", "Dans ton budget"],
            evidence_refs=[
                "editable_preferences.liked_brands[Nike]",
                "hard_constraints.max_price_eur",
            ],
            grounded=True,
            editable_tags=["Nike", "sneakers"],
            sentence="Ce produit correspond à ton style Nike dans ton budget.",
        )
        assert expl.grounded is True
        assert len(expl.reasons) == 2
        assert len(expl.evidence_refs) == 2

    def test_serialization_roundtrip(self):
        expl = Explanation(
            product_id="prod-001",
            reasons=["Style validé"],
            grounded=True,
        )
        restored = Explanation.model_validate_json(expl.model_dump_json())
        assert restored == expl


class TestModuleTrace:
    def test_minimal_instantiation(self):
        trace = ModuleTrace(module="ranking", latency_ms=42.1)
        assert trace.fallback_used is False
        assert trace.warnings == []

    def test_with_fallback(self):
        trace = ModuleTrace(
            module="retrieval",
            latency_ms=110.5,
            warnings=["latency exceeded 100ms target"],
            fallback_used=True,
            version="pgvector-0.7",
        )
        assert trace.fallback_used is True
        assert len(trace.warnings) == 1
