"""Tests for retrieval module -- filters, vector retriever, fallback."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from contracts.product import ProductCondition, ProductRecord, ProductSource
from contracts.profile import (
    HardConstraints,
    StyleVectors,
    UserPreferenceProfile,
)

from retrieval.filters import (
    REGION_SOURCE_MAP,
    HardFilterResult,
    apply_hard_filters,
    matches_hard_filters,
)
from retrieval.fallback import FallbackRetriever, retrieve_with_fallback
from retrieval.retriever import VectorRetriever, _PRODUCT_COLUMNS


# ============================================================================
# Helpers
# ============================================================================

def _product(**overrides) -> ProductRecord:
    defaults = dict(
        id="p1",
        source=ProductSource.ebay,
        source_record_id="ebay-001",
        title="Nike Air Force 1",
        price=45.0,
        currency="EUR",
        condition=ProductCondition.good,
        size_eu="M",
        category="sneakers",
        image_urls=["https://example.com/img.jpg"],
        available=True,
    )
    defaults.update(overrides)
    return ProductRecord(**defaults)


def _profile(**hc_overrides) -> UserPreferenceProfile:
    return UserPreferenceProfile(
        hard_constraints=HardConstraints(**hc_overrides),
    )


def _profile_with_vector(**kwargs) -> UserPreferenceProfile:
    hc_fields = set(HardConstraints.model_fields)
    hc = HardConstraints(**{k: v for k, v in kwargs.items() if k in hc_fields})
    return UserPreferenceProfile(
        hard_constraints=hc,
        vectors=StyleVectors(positive=[0.1] * 768),
        event_count=5,
    )


def _make_db_row(
    product_id: str = "p1",
    similarity: float = 0.9,
    **overrides,
) -> tuple:
    defaults = dict(
        id=product_id,
        source="ebay",
        source_record_id=f"ebay-{product_id}",
        title=f"Product {product_id}",
        brand="Nike",
        model="AF1",
        price=45.0,
        currency="EUR",
        condition="good",
        size_raw="M",
        size_eu="M",
        category="sneakers",
        image_urls=["https://example.com/img.jpg"],
        # The stored column is the raw seller URL; the retriever maps it onto
        # the contract's affiliate_url field.
        listing_url=None,
        available=True,
        enriched_attrs={},
        schema_version=1,
        embedding_version="fashionsiglip-v1",
    )
    defaults.update(overrides)
    return tuple(defaults[c] for c in _PRODUCT_COLUMNS) + (similarity,)


def _mock_conn(rows: list[tuple]) -> MagicMock:
    cursor = MagicMock()
    cursor.fetchall.return_value = rows
    cursor.__enter__ = lambda s: s
    cursor.__exit__ = MagicMock(return_value=False)
    conn = MagicMock()
    conn.cursor.return_value = cursor
    return conn


# ============================================================================
# apply_hard_filters (SQL generation) -- KAN-37
# ============================================================================

class TestApplyHardFiltersEmpty:
    def test_empty_constraints_only_availability(self) -> None:
        result = apply_hard_filters(_profile())
        assert result.applied == ["available"]
        assert result.clauses == ["available = true"]
        assert result.params == {}

    def test_where_sql_with_empty_constraints(self) -> None:
        result = apply_hard_filters(_profile())
        assert result.where_sql == "WHERE available = true"


class TestApplyHardFiltersSize:
    def test_size_clause_added(self) -> None:
        result = apply_hard_filters(_profile(sizes=["M", "L"]))
        assert "size" in result.applied
        assert any("size_eu" in c for c in result.clauses)

    def test_size_params(self) -> None:
        result = apply_hard_filters(_profile(sizes=["M", "L"]))
        assert result.params["filter_sizes"] == ["M", "L"]


class TestApplyHardFiltersPrice:
    def test_price_clause_added(self) -> None:
        result = apply_hard_filters(_profile(max_price_eur=50.0))
        assert "max_price" in result.applied
        assert any("price" in c for c in result.clauses)

    def test_price_params(self) -> None:
        result = apply_hard_filters(_profile(max_price_eur=50.0))
        assert result.params["filter_max_price"] == 50.0


class TestApplyHardFiltersRegion:
    def test_region_clause_added(self) -> None:
        result = apply_hard_filters(_profile(regions=["FR"]))
        assert "region" in result.applied

    def test_region_sources_resolved(self) -> None:
        result = apply_hard_filters(_profile(regions=["FR"]))
        assert result.params["filter_sources"] == sorted(
            REGION_SOURCE_MAP["FR"],
        )

    def test_unknown_region_skipped(self) -> None:
        result = apply_hard_filters(_profile(regions=["XX"]))
        assert "region" not in result.applied
        assert "filter_sources" not in result.params


class TestApplyHardFiltersExcludedConditions:
    def test_excluded_conditions_clause_added(self) -> None:
        result = apply_hard_filters(
            _profile(excluded_conditions=["fair"]),
        )
        assert "excluded_conditions" in result.applied
        assert result.params["filter_excluded_cond"] == ["fair"]


class TestApplyHardFiltersCombined:
    def test_all_filters_combined(self) -> None:
        result = apply_hard_filters(_profile(
            sizes=["M"],
            max_price_eur=100.0,
            regions=["FR"],
            excluded_conditions=["fair"],
        ))
        assert set(result.applied) == {
            "available", "size", "max_price", "region",
            "excluded_conditions",
        }
        assert len(result.clauses) == 5

    def test_where_sql_joins_with_and(self) -> None:
        result = apply_hard_filters(
            _profile(sizes=["M"], max_price_eur=50.0),
        )
        assert " AND " in result.where_sql


class TestHardFilterResult:
    def test_empty_result_no_where(self) -> None:
        assert HardFilterResult().where_sql == ""


# ============================================================================
# matches_hard_filters (in-memory) -- KAN-37
# ============================================================================

class TestMatchesEmpty:
    def test_available_product_passes(self) -> None:
        assert matches_hard_filters(_product(), HardConstraints())

    def test_unavailable_product_rejected(self) -> None:
        assert not matches_hard_filters(
            _product(available=False), HardConstraints(),
        )


class TestMatchesSize:
    def test_matching_size_passes(self) -> None:
        c = HardConstraints(sizes=["M"])
        assert matches_hard_filters(_product(size_eu="M"), c)

    def test_wrong_size_rejected(self) -> None:
        c = HardConstraints(sizes=["M"])
        assert not matches_hard_filters(_product(size_eu="XL"), c)


class TestMatchesPrice:
    def test_under_budget_passes(self) -> None:
        c = HardConstraints(max_price_eur=50.0)
        assert matches_hard_filters(_product(price=45.0), c)

    def test_at_budget_passes(self) -> None:
        c = HardConstraints(max_price_eur=50.0)
        assert matches_hard_filters(_product(price=50.0), c)

    def test_over_budget_rejected(self) -> None:
        c = HardConstraints(max_price_eur=50.0)
        assert not matches_hard_filters(_product(price=75.0), c)


class TestMatchesRegion:
    def test_allowed_source_passes(self) -> None:
        c = HardConstraints(regions=["FR"])
        assert matches_hard_filters(
            _product(source=ProductSource.ebay), c,
        )

    def test_disallowed_source_rejected(self) -> None:
        c = HardConstraints(regions=["DE"])
        assert not matches_hard_filters(
            _product(source=ProductSource.cj), c,
        )


class TestMatchesExcludedConditions:
    def test_excluded_condition_rejected(self) -> None:
        c = HardConstraints(excluded_conditions=["fair"])
        assert not matches_hard_filters(
            _product(condition=ProductCondition.fair), c,
        )

    def test_allowed_condition_passes(self) -> None:
        c = HardConstraints(excluded_conditions=["fair"])
        assert matches_hard_filters(
            _product(condition=ProductCondition.good), c,
        )


class TestMatchesFullScenario:
    def test_size_m_budget_50_filters_correctly(self) -> None:
        """AC: profile size M + budget 50, no XL or >50 in result."""
        c = HardConstraints(sizes=["M"], max_price_eur=50.0)
        products = [
            _product(id="ok1", size_eu="M", price=45.0),
            _product(id="bad-size", size_eu="XL", price=30.0),
            _product(id="bad-price", size_eu="M", price=75.0),
            _product(id="bad-both", size_eu="XL", price=80.0),
            _product(id="ok2", size_eu="M", price=50.0),
        ]
        passing = [p for p in products if matches_hard_filters(p, c)]
        passing_ids = {p.id for p in passing}
        assert passing_ids == {"ok1", "ok2"}
        assert not any(p.size_eu == "XL" for p in passing)
        assert not any(p.price > 50.0 for p in passing)


# ============================================================================
# VectorRetriever -- KAN-38
# ============================================================================

class TestVectorRetrieverColdStart:
    def test_cold_start_returns_empty_candidates(self) -> None:
        conn = _mock_conn([])
        retriever = VectorRetriever(lambda: conn)
        result = retriever.retrieve(_profile())
        assert result.candidates == []
        assert result.retrieval_latency_ms == 0.0
        conn.cursor.assert_not_called()


class TestVectorRetrieverQuery:
    def test_executes_query_with_style_vector(self) -> None:
        conn = _mock_conn([])
        retriever = VectorRetriever(lambda: conn)
        profile = _profile_with_vector()
        with patch("retrieval.retriever.get_disabled_watcher_sources", return_value=[]):
            retriever.retrieve(profile, k=50)
        cursor = conn.cursor.return_value
        cursor.execute.assert_called_once()
        sql, params = cursor.execute.call_args[0]
        assert "embedding <=>" in sql
        # pgvector needs the '[a,b,c]' literal: a Python list is adapted as a
        # Postgres ARRAY, which does not cast to vector.
        assert params["style_vector"] == "[" + ",".join(
            str(v) for v in profile.vectors.positive
        ) + "]"
        assert params["k"] == 50

    def test_hard_filters_in_where_clause(self) -> None:
        conn = _mock_conn([])
        retriever = VectorRetriever(lambda: conn)
        profile = _profile_with_vector(sizes=["M"], max_price_eur=50.0)
        retriever.retrieve(profile)
        sql, params = conn.cursor.return_value.execute.call_args[0]
        assert "size_eu" in sql
        assert "price" in sql
        assert params["filter_sizes"] == ["M"]
        assert params["filter_max_price"] == 50.0


class TestVectorRetrieverResults:
    def test_maps_rows_to_candidate_items(self) -> None:
        rows = [
            _make_db_row("p1", 0.95),
            _make_db_row("p2", 0.80),
        ]
        conn = _mock_conn(rows)
        retriever = VectorRetriever(lambda: conn)
        result = retriever.retrieve(_profile_with_vector())
        assert len(result.candidates) == 2
        assert result.candidates[0].product.id == "p1"
        assert result.candidates[0].similarity_score == 0.95
        assert result.candidates[0].retrieval_rank == 1
        assert result.candidates[1].product.id == "p2"
        assert result.candidates[1].similarity_score == 0.80
        assert result.candidates[1].retrieval_rank == 2

    def test_hard_filters_applied_field_populated(self) -> None:
        conn = _mock_conn([])
        retriever = VectorRetriever(lambda: conn)
        profile = _profile_with_vector(sizes=["M"])
        result = retriever.retrieve(profile)
        assert "size" in result.hard_filters_applied
        assert "available" in result.hard_filters_applied

    def test_latency_is_recorded(self) -> None:
        conn = _mock_conn([])
        retriever = VectorRetriever(lambda: conn)
        result = retriever.retrieve(_profile_with_vector())
        assert result.retrieval_latency_ms >= 0.0

    def test_fallback_used_is_false(self) -> None:
        conn = _mock_conn([])
        retriever = VectorRetriever(lambda: conn)
        result = retriever.retrieve(_profile_with_vector())
        assert result.fallback_used is False


class TestVectorRetrieverGoldenScenario:
    def test_top_10_expected_products_in_top_100(self) -> None:
        """AC: 10 expected products appear in top 100 (Recall@100)."""
        expected_ids = {f"expected-{i}" for i in range(10)}
        rows = []
        for i in range(10):
            rows.append(_make_db_row(
                f"expected-{i}", similarity=0.99 - i * 0.01,
            ))
        for i in range(90):
            rows.append(_make_db_row(
                f"filler-{i}", similarity=0.80 - i * 0.005,
            ))

        conn = _mock_conn(rows)
        retriever = VectorRetriever(lambda: conn)
        result = retriever.retrieve(_profile_with_vector(), k=100)

        retrieved_ids = {c.product.id for c in result.candidates}
        recall = len(expected_ids & retrieved_ids) / len(expected_ids)
        assert recall == 1.0
        assert len(result.candidates) == 100


class TestVectorRetrieverProductParsing:
    def test_source_enum_parsed(self) -> None:
        rows = [_make_db_row("p1", 0.9, source="awin")]
        conn = _mock_conn(rows)
        retriever = VectorRetriever(lambda: conn)
        result = retriever.retrieve(_profile_with_vector())
        assert result.candidates[0].product.source == ProductSource.awin

    def test_condition_enum_parsed(self) -> None:
        rows = [_make_db_row("p1", 0.9, condition="like_new")]
        conn = _mock_conn(rows)
        retriever = VectorRetriever(lambda: conn)
        result = retriever.retrieve(_profile_with_vector())
        assert (
            result.candidates[0].product.condition
            == ProductCondition.like_new
        )


# ============================================================================
# FallbackRetriever -- KAN-39
# ============================================================================

def _make_fallback_row(product_id: str = "p1", **overrides) -> tuple:
    from retrieval.fallback import _DB_COLUMNS
    defaults = dict(
        id=product_id,
        source="ebay",
        source_record_id=f"ebay-{product_id}",
        title=f"Product {product_id}",
        price=45.0,
        condition="good",
        category="sneakers",
        image_urls=["https://example.com/img.jpg"],
        size_raw="M",
        size_eu="M",
        brand="Nike",
        model="AF1",
        embedding_version="fashionsiglip-v1",
        listing_url=None,
    )
    defaults.update(overrides)
    return tuple(defaults[c] for c in _DB_COLUMNS)


class TestFallbackRetriever:
    def test_returns_candidates_with_neutral_scores(self) -> None:
        rows = [_make_fallback_row("f1"), _make_fallback_row("f2")]
        conn = _mock_conn(rows)
        fb = FallbackRetriever(lambda: conn)
        result = fb.retrieve(_profile())
        assert len(result.candidates) == 2
        assert all(c.similarity_score == 0.0 for c in result.candidates)

    def test_fallback_used_flag_is_true(self) -> None:
        conn = _mock_conn([_make_fallback_row("f1")])
        fb = FallbackRetriever(lambda: conn)
        result = fb.retrieve(_profile())
        assert result.fallback_used is True

    def test_hard_filters_applied_populated(self) -> None:
        conn = _mock_conn([])
        fb = FallbackRetriever(lambda: conn)
        result = fb.retrieve(_profile(sizes=["M"]))
        assert "size" in result.hard_filters_applied

    def test_query_orders_by_created_at_desc(self) -> None:
        conn = _mock_conn([])
        fb = FallbackRetriever(lambda: conn)
        fb.retrieve(_profile())
        sql, _ = conn.cursor.return_value.execute.call_args[0]
        assert "created_at DESC" in sql

    def test_logs_warning(self) -> None:
        conn = _mock_conn([])
        fb = FallbackRetriever(lambda: conn)
        with patch("retrieval.fallback._LOG") as mock_log:
            fb.retrieve(_profile())
            mock_log.warning.assert_called_once()

    def test_retrieval_rank_assigned(self) -> None:
        rows = [_make_fallback_row("f1"), _make_fallback_row("f2")]
        conn = _mock_conn(rows)
        fb = FallbackRetriever(lambda: conn)
        result = fb.retrieve(_profile())
        assert result.candidates[0].retrieval_rank == 1
        assert result.candidates[1].retrieval_rank == 2


class TestRetrieveWithFallback:
    def test_uses_vector_retriever_on_success(self) -> None:
        vec_conn = _mock_conn([_make_db_row("v1", 0.95)])
        fb_conn = _mock_conn([_make_fallback_row("f1")])
        vec = VectorRetriever(lambda: vec_conn)
        fb = FallbackRetriever(lambda: fb_conn)
        result = retrieve_with_fallback(vec, fb, _profile_with_vector())
        assert result.candidates[0].product.id == "v1"
        assert result.fallback_used is False

    def test_falls_back_on_vector_exception(self) -> None:
        """AC: VectorRetriever raises -> FallbackRetriever takes over."""
        vec = MagicMock(spec=VectorRetriever)
        vec.retrieve.side_effect = RuntimeError("pgvector down")
        fb_conn = _mock_conn([_make_fallback_row("f1")])
        fb = FallbackRetriever(lambda: fb_conn)
        result = retrieve_with_fallback(vec, fb, _profile_with_vector())
        assert result.fallback_used is True
        assert result.candidates[0].product.id == "f1"
        assert result.candidates[0].similarity_score == 0.0
