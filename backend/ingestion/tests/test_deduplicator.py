"""Tests for ingestion.deduplicator — deduplicate(records) -> list[ProductRecord]."""
from __future__ import annotations

import pytest

from contracts.product import ProductCondition, ProductRecord, ProductSource
from ingestion.deduplicator import _fingerprint, deduplicate

# ── Helpers ───────────────────────────────────────────────────────────────────

_IMG = ["https://img.example.com/a.jpg"]


def _rec(
    record_id: str = "ebay-001",
    source: ProductSource = ProductSource.ebay,
    title: str = "Nike Air Force 1",
    brand: str | None = "Nike",
    model: str | None = "Air Force 1",
    size_eu: str | None = "42",
    condition: ProductCondition = ProductCondition.good,
    price: float = 80.0,
    available: bool = True,
    **kwargs,
) -> ProductRecord:
    return ProductRecord(
        id=record_id,
        source=source,
        source_record_id=record_id.split("-", 1)[-1],
        title=title,
        brand=brand,
        model=model,
        size_eu=size_eu,
        condition=condition,
        price=price,
        currency="EUR",
        category="sneakers",
        image_urls=_IMG,
        available=available,
        **kwargs,
    )


# ── Critère d'acceptation principal ──────────────────────────────────────────

class TestMainAC:
    def test_two_records_same_fingerprint_different_sources_give_one_available(self) -> None:
        """AC: deux ProductRecord quasi identiques venant de deux sources
        donnent un seul produit disponible dans le catalogue."""
        ebay_rec = _rec("ebay-001", ProductSource.ebay, price=95.0)
        awin_rec = _rec("awin-001", ProductSource.awin, price=80.0)

        result = deduplicate([ebay_rec, awin_rec])

        available = [r for r in result if r.available]
        unavailable = [r for r in result if not r.available]
        assert len(available) == 1, "Exactly one record should remain available"
        assert len(unavailable) == 1, "The other should be marked unavailable"

    def test_cheapest_is_kept_available(self) -> None:
        ebay_rec = _rec("ebay-001", ProductSource.ebay, price=95.0)
        awin_rec = _rec("awin-001", ProductSource.awin, price=80.0)

        result = deduplicate([ebay_rec, awin_rec])

        available = next(r for r in result if r.available)
        assert available.price == 80.0
        assert available.source == ProductSource.awin

    def test_more_expensive_is_marked_unavailable(self) -> None:
        ebay_rec = _rec("ebay-001", ProductSource.ebay, price=95.0)
        awin_rec = _rec("awin-001", ProductSource.awin, price=80.0)

        result = deduplicate([ebay_rec, awin_rec])

        dup = next(r for r in result if not r.available)
        assert dup.price == 95.0
        assert dup.source == ProductSource.ebay


# ── Fingerprint ───────────────────────────────────────────────────────────────

class TestFingerprint:
    def test_same_brand_model_size_condition_give_same_fingerprint(self) -> None:
        a = _rec("ebay-001")
        b = _rec("awin-001", source=ProductSource.awin)
        assert _fingerprint(a) == _fingerprint(b)

    def test_different_brand_gives_different_fingerprint(self) -> None:
        a = _rec("ebay-001", brand="Nike")
        b = _rec("ebay-002", brand="Adidas")
        assert _fingerprint(a) != _fingerprint(b)

    def test_different_size_gives_different_fingerprint(self) -> None:
        a = _rec("ebay-001", size_eu="42")
        b = _rec("ebay-002", size_eu="44")
        assert _fingerprint(a) != _fingerprint(b)

    def test_different_condition_gives_different_fingerprint(self) -> None:
        a = _rec("ebay-001", condition=ProductCondition.new)
        b = _rec("ebay-002", condition=ProductCondition.good)
        assert _fingerprint(a) != _fingerprint(b)

    def test_brand_comparison_is_case_insensitive(self) -> None:
        a = _rec("ebay-001", brand="NIKE")
        b = _rec("ebay-002", brand="nike")
        assert _fingerprint(a) == _fingerprint(b)

    def test_no_brand_no_model_gives_unique_fingerprint_per_record(self) -> None:
        a = _rec("ebay-001", brand=None, model=None)
        b = _rec("ebay-002", brand=None, model=None)
        assert _fingerprint(a) != _fingerprint(b)


# ── Comportement de deduplicate ───────────────────────────────────────────────

class TestDeduplicate:
    def test_no_duplicates_all_records_returned(self) -> None:
        nike = _rec("ebay-001", brand="Nike", model="Air Force 1", size_eu="42")
        adidas = _rec("ebay-002", brand="Adidas", model="Gazelle", size_eu="41")
        result = deduplicate([nike, adidas])
        assert len(result) == 2
        assert all(r.available for r in result)

    def test_three_duplicates_one_available_two_not(self) -> None:
        recs = [
            _rec("ebay-001", price=100.0),
            _rec("awin-001", source=ProductSource.awin, price=85.0),
            _rec("ebay-002", price=90.0),
        ]
        result = deduplicate(recs)
        available = [r for r in result if r.available]
        assert len(available) == 1
        assert available[0].price == 85.0

    def test_result_length_equals_input_length(self) -> None:
        recs = [
            _rec("ebay-001", price=100.0),
            _rec("awin-001", source=ProductSource.awin, price=85.0),
            _rec("ebay-002", brand="Adidas", model="Gazelle"),
        ]
        result = deduplicate(recs)
        assert len(result) == 3

    def test_empty_list_returns_empty(self) -> None:
        assert deduplicate([]) == []

    def test_single_record_returned_unchanged(self) -> None:
        rec = _rec("ebay-001")
        result = deduplicate([rec])
        assert len(result) == 1
        assert result[0] is rec

    def test_original_records_not_mutated(self) -> None:
        expensive = _rec("ebay-001", price=100.0)
        cheap = _rec("awin-001", source=ProductSource.awin, price=80.0)
        deduplicate([expensive, cheap])
        assert expensive.available is True
        assert cheap.available is True

    def test_records_without_brand_or_model_are_kept_unique(self) -> None:
        a = _rec("ebay-001", brand=None, model=None, title="Sac mystère")
        b = _rec("ebay-002", brand=None, model=None, title="Sac mystère")
        result = deduplicate([a, b])
        assert all(r.available for r in result)

    def test_mixed_identified_and_anonymous_records(self) -> None:
        identified_a = _rec("ebay-001", price=100.0)
        identified_b = _rec("awin-001", source=ProductSource.awin, price=80.0)
        anonymous = _rec("ebay-003", brand=None, model=None, title="Accessoire")
        result = deduplicate([identified_a, identified_b, anonymous])
        available = [r for r in result if r.available]
        assert len(available) == 2  # cheapest of identified pair + anonymous
