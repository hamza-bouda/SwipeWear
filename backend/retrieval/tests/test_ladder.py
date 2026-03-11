"""Tests for price ladder builder — KAN-54."""
from __future__ import annotations

from unittest.mock import MagicMock

from contracts.pipeline import MatchConfidence, PriceLadder, PriceLadderEntry
from contracts.product import ProductCondition, ProductSource

from retrieval.ladder import (
    _PRODUCT_COLUMNS,
    _compute_confidence,
    _row_to_product,
    build_price_ladder,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_product_row(
    product_id: str = "p1",
    source: str = "ebay",
    brand: str | None = "Nike",
    model: str | None = "Air Force 1",
    price: float = 45.0,
    condition: str = "good",
    **overrides,
) -> tuple:
    defaults = dict(
        id=product_id,
        source=source,
        source_record_id=f"{source}-{product_id}",
        title=f"Product {product_id}",
        brand=brand,
        model=model,
        price=price,
        currency="EUR",
        condition=condition,
        size_raw="M",
        size_eu="M",
        category="sneakers",
        image_urls=["https://example.com/img.jpg"],
        # The stored column is the raw seller URL; _row_to_product maps it
        # onto the contract's affiliate_url field.
        listing_url=f"https://listing.example.com/{product_id}",
        available=True,
        enriched_attrs={},
        schema_version=1,
        embedding_version="fashionsiglip-v1",
    )
    defaults.update(overrides)
    return tuple(defaults[c] for c in _PRODUCT_COLUMNS)


def _make_candidate_row(
    product_id: str = "c1",
    similarity: float = 0.85,
    **kwargs,
) -> tuple:
    return _make_product_row(product_id=product_id, **kwargs) + (similarity,)


def _mock_conn_for_ladder(
    source_row: tuple | None,
    embedding: list[float] | None,
    candidate_rows: list[tuple],
) -> MagicMock:
    cursors: list[MagicMock] = []

    cursor_product = MagicMock()
    cursor_product.fetchone.return_value = source_row
    cursor_product.__enter__ = lambda s: s
    cursor_product.__exit__ = MagicMock(return_value=False)
    cursors.append(cursor_product)

    cursor_emb = MagicMock()
    cursor_emb.fetchone.return_value = (embedding,) if embedding else None
    cursor_emb.__enter__ = lambda s: s
    cursor_emb.__exit__ = MagicMock(return_value=False)
    cursors.append(cursor_emb)

    cursor_candidates = MagicMock()
    cursor_candidates.fetchall.return_value = candidate_rows
    cursor_candidates.__enter__ = lambda s: s
    cursor_candidates.__exit__ = MagicMock(return_value=False)
    cursors.append(cursor_candidates)

    conn = MagicMock()
    conn.cursor.side_effect = cursors
    return conn


# ── _compute_confidence ──────────────────────────────────────────────────────

class TestComputeConfidence:
    def test_exact_when_brand_and_model_match(self) -> None:
        src = _row_to_product(
            _make_product_row("s1", brand="Nike", model="Air Force 1"),
            _PRODUCT_COLUMNS,
        )
        cand = _row_to_product(
            _make_product_row("c1", brand="Nike", model="Air Force 1"),
            _PRODUCT_COLUMNS,
        )
        assert _compute_confidence(src, cand) == MatchConfidence.exact

    def test_exact_is_case_insensitive(self) -> None:
        src = _row_to_product(
            _make_product_row("s1", brand="nike", model="air force 1"),
            _PRODUCT_COLUMNS,
        )
        cand = _row_to_product(
            _make_product_row("c1", brand="NIKE", model="Air Force 1"),
            _PRODUCT_COLUMNS,
        )
        assert _compute_confidence(src, cand) == MatchConfidence.exact

    def test_similar_when_brand_matches_but_model_differs(self) -> None:
        src = _row_to_product(
            _make_product_row("s1", brand="Nike", model="Air Force 1"),
            _PRODUCT_COLUMNS,
        )
        cand = _row_to_product(
            _make_product_row("c1", brand="Nike", model="Air Max 90"),
            _PRODUCT_COLUMNS,
        )
        assert _compute_confidence(src, cand) == MatchConfidence.similar

    def test_similar_when_brand_differs(self) -> None:
        src = _row_to_product(
            _make_product_row("s1", brand="Nike", model="AF1"),
            _PRODUCT_COLUMNS,
        )
        cand = _row_to_product(
            _make_product_row("c1", brand="Adidas", model="Samba"),
            _PRODUCT_COLUMNS,
        )
        assert _compute_confidence(src, cand) == MatchConfidence.similar

    def test_similar_when_brand_is_none(self) -> None:
        src = _row_to_product(
            _make_product_row("s1", brand=None, model=None),
            _PRODUCT_COLUMNS,
        )
        cand = _row_to_product(
            _make_product_row("c1", brand="Nike", model="AF1"),
            _PRODUCT_COLUMNS,
        )
        assert _compute_confidence(src, cand) == MatchConfidence.similar


# ── build_price_ladder — product not found ───────────────────────────────────

class TestBuildPriceLadderNotFound:
    def test_returns_empty_when_product_missing(self) -> None:
        conn = _mock_conn_for_ladder(None, None, [])
        result = build_price_ladder("missing", lambda: conn)
        assert isinstance(result, PriceLadder)
        assert result.source_product_id == "missing"
        assert result.entries == []
        assert result.latency_ms >= 0.0

    def test_returns_empty_when_no_embedding(self) -> None:
        source_row = _make_product_row("p1")
        conn = _mock_conn_for_ladder(source_row, None, [])
        result = build_price_ladder("p1", lambda: conn)
        assert result.entries == []


# ── build_price_ladder — normal results ──────────────────────────────────────

class TestBuildPriceLadderResults:
    def test_returns_entries_sorted_by_price(self) -> None:
        source_row = _make_product_row("src", price=60.0)
        embedding = [0.1] * 768
        candidates = [
            _make_candidate_row("c1", 0.90, price=80.0, source="awin", condition="new"),
            _make_candidate_row("c2", 0.85, price=30.0, source="ebay", condition="good"),
            _make_candidate_row("c3", 0.88, price=55.0, source="ebay", condition="like_new"),
        ]
        conn = _mock_conn_for_ladder(source_row, embedding, candidates)
        result = build_price_ladder("src", lambda: conn, max_results=15)

        assert len(result.entries) == 3
        prices = [e.price_eur for e in result.entries]
        assert prices == sorted(prices)

    def test_min_max_savings_computed(self) -> None:
        source_row = _make_product_row("src")
        embedding = [0.1] * 768
        candidates = [
            _make_candidate_row("c1", 0.90, price=100.0, condition="new"),
            _make_candidate_row("c2", 0.85, price=40.0, condition="good"),
        ]
        conn = _mock_conn_for_ladder(source_row, embedding, candidates)
        result = build_price_ladder("src", lambda: conn)

        assert result.min_price_eur == 40.0
        assert result.max_price_eur == 100.0
        assert result.savings_pct == 60.0

    def test_mixes_occasion_and_new(self) -> None:
        source_row = _make_product_row("src")
        embedding = [0.1] * 768
        candidates = [
            _make_candidate_row("c1", 0.90, condition="new", source="awin"),
            _make_candidate_row("c2", 0.85, condition="good", source="ebay"),
        ]
        conn = _mock_conn_for_ladder(source_row, embedding, candidates)
        result = build_price_ladder("src", lambda: conn)

        conditions = {e.condition for e in result.entries}
        assert "new" in conditions
        assert "good" in conditions

    def test_is_new_flag_set_correctly(self) -> None:
        source_row = _make_product_row("src")
        embedding = [0.1] * 768
        candidates = [
            _make_candidate_row("c1", 0.90, condition="new"),
            _make_candidate_row("c2", 0.85, condition="good"),
        ]
        conn = _mock_conn_for_ladder(source_row, embedding, candidates)
        result = build_price_ladder("src", lambda: conn)

        new_entries = [e for e in result.entries if e.is_new]
        used_entries = [e for e in result.entries if not e.is_new]
        assert len(new_entries) == 1
        assert len(used_entries) == 1

    def test_max_results_limits_output(self) -> None:
        source_row = _make_product_row("src")
        embedding = [0.1] * 768
        candidates = [
            _make_candidate_row(f"c{i}", 0.90 - i * 0.01, price=10.0 + i)
            for i in range(20)
        ]
        conn = _mock_conn_for_ladder(source_row, embedding, candidates)
        result = build_price_ladder("src", lambda: conn, max_results=5)

        assert len(result.entries) <= 5

    def test_latency_recorded(self) -> None:
        source_row = _make_product_row("src")
        embedding = [0.1] * 768
        conn = _mock_conn_for_ladder(source_row, embedding, [])
        result = build_price_ladder("src", lambda: conn)
        assert result.latency_ms >= 0.0


# ── build_price_ladder — confidence & GLiNER refinement ──────────────────────

class TestBuildPriceLadderConfidence:
    def test_exact_match_brand_model(self) -> None:
        source_row = _make_product_row("src", brand="Nike", model="Air Force 1")
        embedding = [0.1] * 768
        candidates = [
            _make_candidate_row(
                "c1", 0.90,
                brand="Nike", model="Air Force 1",
                price=50.0,
            ),
            _make_candidate_row(
                "c2", 0.85,
                brand="Adidas", model="Samba",
                price=40.0,
            ),
        ]
        conn = _mock_conn_for_ladder(source_row, embedding, candidates)
        result = build_price_ladder("src", lambda: conn)

        exact = [e for e in result.entries if e.confidence == MatchConfidence.exact]
        similar = [e for e in result.entries if e.confidence == MatchConfidence.similar]
        assert len(exact) == 1
        assert exact[0].product_id == "c1"
        assert len(similar) == 1
        assert similar[0].product_id == "c2"


# ── Golden scenario: jacket returns only jackets, sorted price ───────────────

class TestBuildPriceLadderGolden:
    def test_jacket_returns_sorted_mixed_condition(self) -> None:
        source_row = _make_product_row(
            "jacket-1", brand="The North Face", model="Nuptse",
            price=120.0, category="jackets",
        )
        embedding = [0.1] * 768
        candidates = [
            _make_candidate_row(
                "j-used", 0.92, brand="The North Face", model="Nuptse",
                price=75.0, condition="good", source="ebay",
                category="jackets",
            ),
            _make_candidate_row(
                "j-like-new", 0.88, brand="The North Face", model="Nuptse",
                price=95.0, condition="like_new", source="ebay",
                category="jackets",
            ),
            _make_candidate_row(
                "j-new", 0.85, brand="The North Face", model="Nuptse",
                price=180.0, condition="new", source="awin",
                category="jackets",
            ),
        ]
        conn = _mock_conn_for_ladder(source_row, embedding, candidates)
        result = build_price_ladder("jacket-1", lambda: conn)

        assert len(result.entries) == 3
        prices = [e.price_eur for e in result.entries]
        assert prices == [75.0, 95.0, 180.0]

        conditions = [e.condition for e in result.entries]
        assert "new" in conditions
        assert "good" in conditions

        assert all(
            e.confidence == MatchConfidence.exact for e in result.entries
        )

        assert result.savings_pct is not None
        assert result.savings_pct > 0
