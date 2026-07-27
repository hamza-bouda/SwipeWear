"""Tests for the policy module — MMR diversity + epsilon-greedy."""
from __future__ import annotations

import random
from uuid import uuid4

import pytest

from contracts.pipeline import RankedFeed, RankedItem
from contracts.product import ProductCondition, ProductRecord, ProductSource
from policy.diversity import mmr_rerank
from policy.exploration import EXPLORATION_MARKER, epsilon_greedy_inject


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_ranked_item(
    pid: str = "p-001",
    score: float = 0.8,
    rank: int = 1,
    category: str = "sneakers",
    brand: str | None = None,
    **overrides,
) -> RankedItem:
    product = ProductRecord(
        id=pid,
        source=ProductSource.ebay,
        source_record_id=f"src-{pid}",
        title=f"Product {pid}",
        brand=brand,
        price=50.0,
        condition=ProductCondition.good,
        category=category,
        image_urls=["https://img.test.com/1.jpg"],
        size_raw="M",
        size_eu="M",
    )
    return RankedItem(
        product=product,
        final_score=score,
        rank=rank,
        score_breakdown={"similarity": score},
        **overrides,
    )


def _make_feed(*items: RankedItem) -> RankedFeed:
    return RankedFeed(
        request_id=uuid4(),
        items=list(items),
    )


# ── MMR basic ────────────────────────────────────────────────────────────────

class TestMmrBasic:
    def test_returns_ranked_feed(self) -> None:
        feed = _make_feed(_make_ranked_item())
        result = mmr_rerank(feed)
        assert isinstance(result, RankedFeed)

    def test_diversity_applied_set(self) -> None:
        feed = _make_feed(_make_ranked_item())
        result = mmr_rerank(feed)
        assert result.diversity_applied is True

    def test_empty_feed(self) -> None:
        feed = _make_feed()
        result = mmr_rerank(feed)
        assert result.items == []
        assert result.diversity_applied is True

    def test_single_item(self) -> None:
        feed = _make_feed(_make_ranked_item())
        result = mmr_rerank(feed)
        assert len(result.items) == 1

    def test_preserves_request_id(self) -> None:
        feed = _make_feed(_make_ranked_item())
        result = mmr_rerank(feed)
        assert result.request_id == feed.request_id

    def test_all_items_preserved(self) -> None:
        items = [
            _make_ranked_item(f"p-{i}", score=0.9 - i * 0.1, rank=i + 1)
            for i in range(10)
        ]
        feed = _make_feed(*items)
        result = mmr_rerank(feed)
        result_ids = {it.product.id for it in result.items}
        input_ids = {it.product.id for it in items}
        assert result_ids == input_ids

    def test_ranks_reassigned(self) -> None:
        items = [
            _make_ranked_item(f"p-{i}", score=0.9 - i * 0.1, rank=i + 1)
            for i in range(5)
        ]
        feed = _make_feed(*items)
        result = mmr_rerank(feed)
        ranks = [it.rank for it in result.items]
        assert ranks == [1, 2, 3, 4, 5]


# ── Category diversity ───────────────────────────────────────────────────────

class TestCategoryDiversity:
    def test_20_similar_jackets_top5_has_3_categories(self) -> None:
        items = []
        categories = ["vestes", "sneakers", "jeans", "tee-shirts", "accessoires"]
        for i in range(20):
            cat = categories[i % 5]
            items.append(
                _make_ranked_item(
                    f"p-{i}",
                    score=0.9 - i * 0.005,
                    rank=i + 1,
                    category=cat,
                )
            )
        feed = _make_feed(*items)
        result = mmr_rerank(feed, lambda_=0.7)
        top5_categories = {it.product.category for it in result.items[:5]}
        assert len(top5_categories) >= 3

    def test_diverse_items_stay_diverse(self) -> None:
        items = [
            _make_ranked_item("p-1", score=0.9, rank=1, category="sneakers"),
            _make_ranked_item("p-2", score=0.85, rank=2, category="vestes"),
            _make_ranked_item("p-3", score=0.80, rank=3, category="jeans"),
        ]
        feed = _make_feed(*items)
        result = mmr_rerank(feed)
        categories = [it.product.category for it in result.items]
        assert len(set(categories)) == 3

    def test_same_category_penalized(self) -> None:
        items = [
            _make_ranked_item("p-1", score=0.9, rank=1, category="sneakers"),
            _make_ranked_item("p-2", score=0.88, rank=2, category="sneakers"),
            _make_ranked_item("p-3", score=0.85, rank=3, category="vestes"),
        ]
        feed = _make_feed(*items)
        result = mmr_rerank(feed, lambda_=0.5)
        assert result.items[1].product.category == "vestes"


# ── Lambda parameter ─────────────────────────────────────────────────────────

class TestLambdaParameter:
    def test_lambda_1_preserves_original_order(self) -> None:
        items = [
            _make_ranked_item(f"p-{i}", score=0.9 - i * 0.1, rank=i + 1)
            for i in range(5)
        ]
        feed = _make_feed(*items)
        result = mmr_rerank(feed, lambda_=1.0)
        result_ids = [it.product.id for it in result.items]
        assert result_ids == [f"p-{i}" for i in range(5)]

    def test_lambda_0_maximizes_diversity(self) -> None:
        items = [
            _make_ranked_item("p-1", score=0.9, rank=1, category="sneakers"),
            _make_ranked_item("p-2", score=0.88, rank=2, category="sneakers"),
            _make_ranked_item("p-3", score=0.60, rank=3, category="vestes"),
        ]
        feed = _make_feed(*items)
        result = mmr_rerank(feed, lambda_=0.0)
        assert result.items[1].product.category == "vestes"


# ── Embedding-based similarity ───────────────────────────────────────────────

class TestEmbeddingSimilarity:
    def test_with_embeddings_dict(self) -> None:
        items = [
            _make_ranked_item("p-1", score=0.9, rank=1, category="sneakers"),
            _make_ranked_item("p-2", score=0.85, rank=2, category="sneakers"),
            _make_ranked_item("p-3", score=0.80, rank=3, category="sneakers"),
        ]
        embeddings = {
            "p-1": [1.0, 0.0, 0.0],
            "p-2": [0.99, 0.1, 0.0],
            "p-3": [0.0, 1.0, 0.0],
        }
        feed = _make_feed(*items)
        result = mmr_rerank(feed, embeddings=embeddings, lambda_=0.5)
        assert result.items[1].product.id == "p-3"

    def test_without_embeddings_uses_category(self) -> None:
        items = [
            _make_ranked_item("p-1", score=0.9, rank=1, category="sneakers"),
            _make_ranked_item("p-2", score=0.88, rank=2, category="sneakers"),
            _make_ranked_item("p-3", score=0.85, rank=3, category="vestes"),
        ]
        feed = _make_feed(*items)
        result = mmr_rerank(feed, embeddings=None, lambda_=0.5)
        assert result.items[1].product.category == "vestes"


# ── Helpers for exploration ──────────────────────────────────────────────────

def _make_catalogue_product(pid: str, category: str = "sneakers") -> ProductRecord:
    return ProductRecord(
        id=pid,
        source=ProductSource.ebay,
        source_record_id=f"src-{pid}",
        title=f"Catalogue {pid}",
        price=40.0,
        condition=ProductCondition.good,
        category=category,
        image_urls=["https://img.test.com/1.jpg"],
        size_raw="M",
        size_eu="M",
    )


# ── Epsilon-greedy exploration (KAN-43) ──────────────────────────────────────

class TestEpsilonGreedyBasic:
    def test_returns_ranked_feed(self) -> None:
        feed = _make_feed(_make_ranked_item())
        catalogue = [_make_catalogue_product("cat-1")]
        result = epsilon_greedy_inject(feed, catalogue, epsilon=0.5, rng=random.Random(42))
        assert isinstance(result, RankedFeed)

    def test_epsilon_0_no_changes(self) -> None:
        items = [_make_ranked_item(f"p-{i}", rank=i + 1) for i in range(5)]
        feed = _make_feed(*items)
        catalogue = [_make_catalogue_product(f"cat-{i}") for i in range(10)]
        result = epsilon_greedy_inject(feed, catalogue, epsilon=0.0)
        result_ids = [it.product.id for it in result.items]
        assert result_ids == [f"p-{i}" for i in range(5)]

    def test_empty_feed_unchanged(self) -> None:
        feed = _make_feed()
        catalogue = [_make_catalogue_product("cat-1")]
        result = epsilon_greedy_inject(feed, catalogue, epsilon=0.5)
        assert result.items == []

    def test_empty_catalogue_unchanged(self) -> None:
        feed = _make_feed(_make_ranked_item())
        result = epsilon_greedy_inject(feed, [], epsilon=0.5)
        assert len(result.items) == 1

    def test_preserves_request_id(self) -> None:
        feed = _make_feed(_make_ranked_item())
        catalogue = [_make_catalogue_product("cat-1")]
        result = epsilon_greedy_inject(feed, catalogue, epsilon=0.5, rng=random.Random(42))
        assert result.request_id == feed.request_id

    def test_feed_size_preserved(self) -> None:
        items = [_make_ranked_item(f"p-{i}", rank=i + 1) for i in range(10)]
        feed = _make_feed(*items)
        catalogue = [_make_catalogue_product(f"cat-{i}") for i in range(20)]
        result = epsilon_greedy_inject(feed, catalogue, epsilon=0.5, rng=random.Random(42))
        assert len(result.items) == 10


class TestEpsilonGreedyInjection:
    def test_exploration_items_marked(self) -> None:
        items = [_make_ranked_item(f"p-{i}", rank=i + 1) for i in range(20)]
        feed = _make_feed(*items)
        catalogue = [_make_catalogue_product(f"cat-{i}") for i in range(50)]
        result = epsilon_greedy_inject(feed, catalogue, epsilon=0.5, rng=random.Random(42))
        explore_items = [
            it for it in result.items
            if it.score_breakdown.get(EXPLORATION_MARKER, 0.0) > 0
        ]
        assert len(explore_items) > 0

    def test_20_positions_epsilon_0_2_gives_3_to_5_explorations(self) -> None:
        items = [_make_ranked_item(f"p-{i}", rank=i + 1) for i in range(20)]
        feed = _make_feed(*items)
        catalogue = [_make_catalogue_product(f"cat-{i}") for i in range(50)]
        counts = []
        for seed in range(100):
            result = epsilon_greedy_inject(
                feed, catalogue, epsilon=0.2, rng=random.Random(seed),
            )
            n = sum(
                1 for it in result.items
                if it.score_breakdown.get(EXPLORATION_MARKER, 0.0) > 0
            )
            counts.append(n)
        avg = sum(counts) / len(counts)
        assert 2 <= avg <= 6

    def test_no_duplicate_ids(self) -> None:
        items = [_make_ranked_item(f"p-{i}", rank=i + 1) for i in range(10)]
        feed = _make_feed(*items)
        catalogue = [_make_catalogue_product(f"cat-{i}") for i in range(20)]
        result = epsilon_greedy_inject(feed, catalogue, epsilon=0.5, rng=random.Random(42))
        ids = [it.product.id for it in result.items]
        assert len(ids) == len(set(ids))

    def test_exploration_items_have_zero_score(self) -> None:
        items = [_make_ranked_item(f"p-{i}", score=0.9, rank=i + 1) for i in range(10)]
        feed = _make_feed(*items)
        catalogue = [_make_catalogue_product(f"cat-{i}") for i in range(20)]
        result = epsilon_greedy_inject(feed, catalogue, epsilon=0.5, rng=random.Random(42))
        for it in result.items:
            if it.score_breakdown.get(EXPLORATION_MARKER, 0.0) > 0:
                assert it.final_score == 0.0

    def test_ranks_reassigned(self) -> None:
        items = [_make_ranked_item(f"p-{i}", rank=i + 1) for i in range(10)]
        feed = _make_feed(*items)
        catalogue = [_make_catalogue_product(f"cat-{i}") for i in range(20)]
        result = epsilon_greedy_inject(feed, catalogue, epsilon=0.3, rng=random.Random(42))
        ranks = [it.rank for it in result.items]
        assert ranks == list(range(1, 11))

    def test_epsilon_1_replaces_all(self) -> None:
        items = [_make_ranked_item(f"p-{i}", rank=i + 1) for i in range(5)]
        feed = _make_feed(*items)
        catalogue = [_make_catalogue_product(f"cat-{i}") for i in range(20)]
        result = epsilon_greedy_inject(feed, catalogue, epsilon=1.0, rng=random.Random(42))
        explore_count = sum(
            1 for it in result.items
            if it.score_breakdown.get(EXPLORATION_MARKER, 0.0) > 0
        )
        assert explore_count == 5

    def test_catalogue_items_not_in_feed_excluded(self) -> None:
        items = [_make_ranked_item("p-1", rank=1)]
        feed = _make_feed(*items)
        catalogue = [_make_catalogue_product("p-1")]
        result = epsilon_greedy_inject(feed, catalogue, epsilon=0.5, rng=random.Random(42))
        assert len(result.items) == 1
        assert result.items[0].product.id == "p-1"
