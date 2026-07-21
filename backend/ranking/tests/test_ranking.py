"""Tests for the ranking module — TransparentRanker (KAN-41)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from contracts.pipeline import CandidateItem, CandidateSet, RankedFeed
from contracts.product import ProductCondition, ProductRecord, ProductSource
from contracts.profile import (
    EditablePreferences,
    HardConstraints,
    UserPreferenceProfile,
)
from ranking.config import (
    DEFAULT_WEIGHTS,
    FRESHNESS_HALF_LIFE_DAYS,
    PRICE_FIT_THRESHOLD,
    RankingWeights,
)
from ranking.ranker import TransparentRanker


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_product(
    pid: str = "p-001",
    price: float = 50.0,
    brand: str | None = None,
    indexed_at: str | None = None,
    **overrides,
) -> ProductRecord:
    defaults = {
        "id": pid,
        "source": ProductSource.ebay,
        "source_record_id": f"src-{pid}",
        "title": f"Product {pid}",
        "brand": brand,
        "price": price,
        "condition": ProductCondition.good,
        "category": "sneakers",
        "image_urls": ["https://img.test.com/1.jpg"],
        "size_raw": "M",
        "size_eu": "M",
    }
    defaults.update(overrides)
    if indexed_at:
        defaults.setdefault("enriched_attrs", {})["indexed_at"] = indexed_at
    return ProductRecord(**defaults)


def _make_candidate(
    pid: str = "p-001",
    similarity: float = 0.8,
    rank: int = 1,
    **product_kw,
) -> CandidateItem:
    return CandidateItem(
        product=_make_product(pid=pid, **product_kw),
        similarity_score=similarity,
        retrieval_rank=rank,
    )


def _make_candidate_set(*candidates: CandidateItem) -> CandidateSet:
    return CandidateSet(
        request_id=uuid4(),
        candidates=list(candidates),
    )


def _make_profile(
    max_price: float | None = 100.0,
    liked_brands: list[str] | None = None,
) -> UserPreferenceProfile:
    return UserPreferenceProfile(
        hard_constraints=HardConstraints(max_price_eur=max_price),
        editable_preferences=EditablePreferences(
            liked_brands=liked_brands or [],
        ),
    )


# ── TransparentRanker basic ──────────────────────────────────────────────────

class TestTransparentRankerBasic:
    def test_returns_ranked_feed(self) -> None:
        cs = _make_candidate_set(_make_candidate())
        feed = TransparentRanker().rank(cs, _make_profile())
        assert isinstance(feed, RankedFeed)
        assert len(feed.items) == 1

    def test_items_sorted_by_final_score_desc(self) -> None:
        c1 = _make_candidate("p-1", similarity=0.9, rank=1, price=50.0)
        c2 = _make_candidate("p-2", similarity=0.3, rank=2, price=50.0)
        cs = _make_candidate_set(c1, c2)
        feed = TransparentRanker().rank(cs, _make_profile())
        assert feed.items[0].product.id == "p-1"
        assert feed.items[1].product.id == "p-2"
        assert feed.items[0].final_score >= feed.items[1].final_score

    def test_rank_assigned_sequentially(self) -> None:
        cs = _make_candidate_set(
            _make_candidate("p-1", similarity=0.9, rank=1),
            _make_candidate("p-2", similarity=0.5, rank=2),
            _make_candidate("p-3", similarity=0.3, rank=3),
        )
        feed = TransparentRanker().rank(cs, _make_profile())
        ranks = [it.rank for it in feed.items]
        assert ranks == [1, 2, 3]

    def test_empty_candidates(self) -> None:
        cs = _make_candidate_set()
        feed = TransparentRanker().rank(cs, _make_profile())
        assert feed.items == []

    def test_request_id_preserved(self) -> None:
        rid = uuid4()
        cs = CandidateSet(request_id=rid, candidates=[])
        feed = TransparentRanker().rank(cs, _make_profile())
        assert feed.request_id == rid

    def test_latency_recorded(self) -> None:
        cs = _make_candidate_set(_make_candidate())
        feed = TransparentRanker().rank(cs, _make_profile())
        assert feed.ranking_latency_ms >= 0.0


# ── Score breakdown ──────────────────────────────────────────────────────────

class TestScoreBreakdown:
    def test_breakdown_has_all_features(self) -> None:
        cs = _make_candidate_set(_make_candidate())
        feed = TransparentRanker().rank(cs, _make_profile())
        bd = feed.items[0].score_breakdown
        assert "similarity" in bd
        assert "price_fit" in bd
        assert "brand_boost" in bd
        assert "freshness" in bd

    def test_final_score_is_weighted_sum(self) -> None:
        w = DEFAULT_WEIGHTS
        cs = _make_candidate_set(_make_candidate(similarity=0.7, price=60.0))
        feed = TransparentRanker().rank(cs, _make_profile(max_price=100.0))
        bd = feed.items[0].score_breakdown
        expected = (
            w.similarity * bd["similarity"]
            + w.price_fit * bd["price_fit"]
            + w.brand_boost * bd["brand_boost"]
            + w.freshness * bd["freshness"]
        )
        assert abs(feed.items[0].final_score - expected) < 1e-4


# ── Similarity feature ───────────────────────────────────────────────────────

class TestSimilarityFeature:
    def test_similarity_passes_through(self) -> None:
        cs = _make_candidate_set(_make_candidate(similarity=0.85))
        feed = TransparentRanker().rank(cs, _make_profile())
        assert abs(feed.items[0].score_breakdown["similarity"] - 0.85) < 1e-4

    def test_higher_similarity_ranks_higher(self) -> None:
        c1 = _make_candidate("p-1", similarity=0.95, rank=1, price=50.0)
        c2 = _make_candidate("p-2", similarity=0.60, rank=2, price=50.0)
        cs = _make_candidate_set(c1, c2)
        feed = TransparentRanker().rank(cs, _make_profile())
        assert feed.items[0].product.id == "p-1"


# ── Price fit feature ────────────────────────────────────────────────────────

class TestPriceFitFeature:
    def test_under_80_percent_budget_is_1(self) -> None:
        cs = _make_candidate_set(_make_candidate(price=70.0))
        feed = TransparentRanker().rank(cs, _make_profile(max_price=100.0))
        assert feed.items[0].score_breakdown["price_fit"] == 1.0

    def test_at_budget_is_0(self) -> None:
        cs = _make_candidate_set(_make_candidate(price=100.0))
        feed = TransparentRanker().rank(cs, _make_profile(max_price=100.0))
        assert abs(feed.items[0].score_breakdown["price_fit"]) < 1e-4

    def test_over_budget_is_0(self) -> None:
        cs = _make_candidate_set(_make_candidate(price=120.0))
        feed = TransparentRanker().rank(cs, _make_profile(max_price=100.0))
        assert feed.items[0].score_breakdown["price_fit"] == 0.0

    def test_no_budget_gives_neutral(self) -> None:
        cs = _make_candidate_set(_make_candidate(price=50.0))
        feed = TransparentRanker().rank(cs, _make_profile(max_price=None))
        assert feed.items[0].score_breakdown["price_fit"] == 0.5

    def test_exactly_at_threshold(self) -> None:
        cs = _make_candidate_set(_make_candidate(price=80.0))
        feed = TransparentRanker().rank(cs, _make_profile(max_price=100.0))
        assert feed.items[0].score_breakdown["price_fit"] == 1.0

    def test_between_threshold_and_budget(self) -> None:
        cs = _make_candidate_set(_make_candidate(price=90.0))
        feed = TransparentRanker().rank(cs, _make_profile(max_price=100.0))
        pf = feed.items[0].score_breakdown["price_fit"]
        assert 0.0 < pf < 1.0


# ── Brand boost feature ─────────────────────────────────────────────────────

class TestBrandBoostFeature:
    def test_liked_brand_gets_boost(self) -> None:
        cs = _make_candidate_set(_make_candidate(brand="Nike"))
        profile = _make_profile(liked_brands=["Nike"])
        feed = TransparentRanker().rank(cs, profile)
        assert feed.items[0].score_breakdown["brand_boost"] == 1.0

    def test_liked_brand_case_insensitive(self) -> None:
        cs = _make_candidate_set(_make_candidate(brand="nike"))
        profile = _make_profile(liked_brands=["NIKE"])
        feed = TransparentRanker().rank(cs, profile)
        assert feed.items[0].score_breakdown["brand_boost"] == 1.0

    def test_non_liked_brand_no_boost(self) -> None:
        cs = _make_candidate_set(_make_candidate(brand="Adidas"))
        profile = _make_profile(liked_brands=["Nike"])
        feed = TransparentRanker().rank(cs, profile)
        assert feed.items[0].score_breakdown["brand_boost"] == 0.0

    def test_no_brand_no_boost(self) -> None:
        cs = _make_candidate_set(_make_candidate(brand=None))
        profile = _make_profile(liked_brands=["Nike"])
        feed = TransparentRanker().rank(cs, profile)
        assert feed.items[0].score_breakdown["brand_boost"] == 0.0

    def test_liked_brand_ranks_higher_at_equal_similarity(self) -> None:
        c1 = _make_candidate("p-nike", similarity=0.8, rank=1, brand="Nike", price=50.0)
        c2 = _make_candidate("p-other", similarity=0.8, rank=2, brand="Adidas", price=50.0)
        cs = _make_candidate_set(c1, c2)
        profile = _make_profile(liked_brands=["Nike"])
        feed = TransparentRanker().rank(cs, profile)
        assert feed.items[0].product.id == "p-nike"
        assert feed.items[0].final_score > feed.items[1].final_score


# ── Freshness feature ────────────────────────────────────────────────────────

class TestFreshnessFeature:
    def test_fresh_product_high_score(self) -> None:
        now = datetime.now(timezone.utc)
        cs = _make_candidate_set(
            _make_candidate(indexed_at=now.isoformat()),
        )
        feed = TransparentRanker().rank(cs, _make_profile())
        assert feed.items[0].score_breakdown["freshness"] > 0.9

    def test_old_product_low_score(self) -> None:
        old = datetime.now(timezone.utc) - timedelta(days=30)
        cs = _make_candidate_set(
            _make_candidate(indexed_at=old.isoformat()),
        )
        feed = TransparentRanker().rank(cs, _make_profile())
        assert feed.items[0].score_breakdown["freshness"] < 0.2

    def test_no_indexed_at_gives_neutral(self) -> None:
        cs = _make_candidate_set(_make_candidate())
        feed = TransparentRanker().rank(cs, _make_profile())
        assert feed.items[0].score_breakdown["freshness"] == 0.5

    def test_half_life_is_7_days(self) -> None:
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        cs = _make_candidate_set(
            _make_candidate(indexed_at=seven_days_ago.isoformat()),
        )
        feed = TransparentRanker().rank(cs, _make_profile())
        assert abs(feed.items[0].score_breakdown["freshness"] - 0.5) < 0.05


# ── Custom weights ───────────────────────────────────────────────────────────

class TestCustomWeights:
    def test_similarity_only_weights(self) -> None:
        w = RankingWeights(similarity=1.0, price_fit=0.0, brand_boost=0.0, freshness=0.0)
        c1 = _make_candidate("p-1", similarity=0.9, rank=1, price=50.0)
        c2 = _make_candidate("p-2", similarity=0.5, rank=2, price=50.0, brand="Nike")
        cs = _make_candidate_set(c1, c2)
        profile = _make_profile(liked_brands=["Nike"])
        feed = TransparentRanker(weights=w).rank(cs, profile)
        assert feed.items[0].product.id == "p-1"

    def test_brand_only_weights(self) -> None:
        w = RankingWeights(similarity=0.0, price_fit=0.0, brand_boost=1.0, freshness=0.0)
        c1 = _make_candidate("p-1", similarity=0.9, rank=1, price=50.0)
        c2 = _make_candidate("p-2", similarity=0.3, rank=2, price=50.0, brand="Nike")
        cs = _make_candidate_set(c1, c2)
        profile = _make_profile(liked_brands=["Nike"])
        feed = TransparentRanker(weights=w).rank(cs, profile)
        assert feed.items[0].product.id == "p-2"


# ── Config defaults ──────────────────────────────────────────────────────────

class TestConfig:
    def test_default_weights_sum_to_1(self) -> None:
        w = DEFAULT_WEIGHTS
        total = w.similarity + w.price_fit + w.brand_boost + w.freshness
        assert abs(total - 1.0) < 1e-6

    def test_price_fit_threshold_is_0_8(self) -> None:
        assert PRICE_FIT_THRESHOLD == 0.80

    def test_freshness_half_life_is_7(self) -> None:
        assert FRESHNESS_HALF_LIFE_DAYS == 7.0

    def test_weights_are_frozen(self) -> None:
        with pytest.raises(AttributeError):
            DEFAULT_WEIGHTS.similarity = 0.99
