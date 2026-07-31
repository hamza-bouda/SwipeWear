"""Tests for retrieval/filters.py -- hard filters (KAN-37)."""
from __future__ import annotations

from contracts.product import ProductCondition, ProductRecord, ProductSource
from contracts.profile import HardConstraints, UserPreferenceProfile

from retrieval.filters import (
    REGION_SOURCE_MAP,
    HardFilterResult,
    apply_hard_filters,
    matches_hard_filters,
)


# -- Helpers ------------------------------------------------------------------

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


# -- apply_hard_filters (SQL generation) -------------------------------------

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
            REGION_SOURCE_MAP["FR"]
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


# -- HardFilterResult --------------------------------------------------------

class TestHardFilterResult:
    def test_empty_result_no_where(self) -> None:
        assert HardFilterResult().where_sql == ""


# -- matches_hard_filters (in-memory) ----------------------------------------

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
