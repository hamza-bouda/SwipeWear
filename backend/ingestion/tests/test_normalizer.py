"""Tests for ingestion.normalizer — normalize(source, raw) -> ProductRecord."""
from __future__ import annotations

import pytest

from contracts.product import ProductCondition, ProductRecord, ProductSource
from ingestion.normalizer import (
    NormalizationError,
    _normalize_category,
    _normalize_condition,
    _normalize_size,
    _to_eur,
    normalize,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

_IMG = ["https://i.ebayimg.com/img.jpg"]


def _raw(
    item_id: str = "v1|001|0",
    title: str = "Nike Air Max 90 Taille M",
    price: float = 89.99,
    currency: str = "EUR",
    condition: str = "USED",
    image_urls: list[str] | None = None,
    **extra,
) -> dict:
    base = {
        "item_id": item_id,
        "title": title,
        "price": price,
        "currency": currency,
        "condition": condition,
        "image_urls": image_urls if image_urls is not None else _IMG,
        "listing_url": "https://www.ebay.fr/itm/001",
        "source": "ebay",
        "size_raw": "M",
    }
    base.update(extra)
    return base


# ── 10 valid eBay raws → 10 ProductRecords ────────────────────────────────────

_VALID_RAWS = [
    _raw("e001", "Nike Air Max 90 M", 89.99, condition="USED", size_raw="M"),
    _raw("e002", "Adidas Gazelle 42", 55.0, condition="LIKE_NEW", size_raw="42"),
    _raw("e003", "Levi's 501 Jeans W32", 45.0, condition="GOOD", size_raw="32"),
    _raw("e004", "Veste The North Face XL", 120.0, condition="VERY_GOOD", size_raw="XL"),
    _raw("e005", "Tee-shirt Lacoste S", 25.0, condition="NEW", size_raw="S"),
    _raw("e006", "Sac à main Longchamp", 60.0, condition="ACCEPTABLE", size_raw=None),
    _raw("e007", "Chaussures Nike 40", 75.0, currency="USD", condition="good", size_raw="40"),
    _raw("e008", "Manteau Zara L", 85.0, currency="GBP", condition="like_new", size_raw="L"),
    _raw("e009", "Baskets Puma EU 38", 40.0, condition="USED", size_raw="EU 38"),
    _raw("e010", "Jean Slim H&M 36", 30.0, condition="fair", size_raw="36"),
]


class TestNormalizeBatch:
    def test_10_valid_raws_produce_10_productrecords(self):
        results = [normalize("ebay", r) for r in _VALID_RAWS]
        assert len(results) == 10
        assert all(isinstance(r, ProductRecord) for r in results)

    def test_all_results_have_eur_currency(self):
        for r in _VALID_RAWS:
            rec = normalize("ebay", r)
            assert rec.currency == "EUR"

    def test_all_results_have_positive_price(self):
        for r in _VALID_RAWS:
            rec = normalize("ebay", r)
            assert rec.price > 0

    def test_all_results_have_source_ebay(self):
        for r in _VALID_RAWS:
            rec = normalize("ebay", r)
            assert rec.source == ProductSource.ebay

    def test_all_results_have_non_empty_image_urls(self):
        for r in _VALID_RAWS:
            rec = normalize("ebay", r)
            assert len(rec.image_urls) >= 1

    def test_all_results_have_valid_category(self):
        valid = {"sneakers", "vestes", "jeans", "tee-shirts", "accessoires"}
        for r in _VALID_RAWS:
            rec = normalize("ebay", r)
            assert rec.category in valid

    def test_id_is_prefixed_with_source(self):
        rec = normalize("ebay", _raw("v1|001|0"))
        assert rec.id.startswith("ebay-")

    def test_source_record_id_is_item_id(self):
        rec = normalize("ebay", _raw("v1|001|0"))
        assert rec.source_record_id == "v1|001|0"


# ── NormalizationError — negative tests ───────────────────────────────────────

class TestNormalizationErrors:
    def test_missing_item_id_raises(self):
        with pytest.raises(NormalizationError, match="item_id"):
            normalize("ebay", {**_raw(), "item_id": ""})

    def test_missing_title_raises(self):
        with pytest.raises(NormalizationError, match="title"):
            normalize("ebay", {**_raw(), "title": ""})

    def test_missing_price_raises(self):
        r = {k: v for k, v in _raw().items() if k != "price"}
        with pytest.raises(NormalizationError, match="price"):
            normalize("ebay", r)

    def test_zero_price_raises(self):
        with pytest.raises(NormalizationError, match="price"):
            normalize("ebay", {**_raw(), "price": 0})

    def test_negative_price_raises(self):
        with pytest.raises(NormalizationError, match="price"):
            normalize("ebay", {**_raw(), "price": -5.0})

    def test_non_numeric_price_raises(self):
        with pytest.raises(NormalizationError, match="price"):
            normalize("ebay", {**_raw(), "price": "not-a-number"})

    def test_empty_image_urls_raises(self):
        with pytest.raises(NormalizationError, match="image_urls"):
            normalize("ebay", {**_raw(), "image_urls": []})

    def test_missing_image_urls_raises(self):
        r = {k: v for k, v in _raw().items() if k != "image_urls"}
        with pytest.raises(NormalizationError, match="image_urls"):
            normalize("ebay", r)

    def test_unknown_source_raises(self):
        with pytest.raises(NormalizationError, match="source"):
            normalize("vinted", _raw())

    def test_unsupported_currency_raises(self):
        with pytest.raises(NormalizationError, match="currency"):
            normalize("ebay", {**_raw(), "currency": "JPY"})

    def test_error_message_contains_item_id(self):
        with pytest.raises(NormalizationError, match="e999"):
            normalize("ebay", {**_raw("e999"), "title": ""})


# ── Currency conversion ───────────────────────────────────────────────────────

class TestCurrencyConversion:
    def test_eur_unchanged(self):
        assert _to_eur(100.0, "EUR") == 100.0

    def test_usd_to_eur(self):
        result = _to_eur(100.0, "USD")
        assert result == round(100.0 * 0.92, 2)

    def test_gbp_to_eur(self):
        result = _to_eur(50.0, "GBP")
        assert result == round(50.0 * 1.17, 2)

    def test_lowercase_currency_accepted(self):
        result = _to_eur(100.0, "usd")
        assert result > 0

    def test_unsupported_currency_raises(self):
        with pytest.raises(NormalizationError, match="JPY"):
            _to_eur(100.0, "JPY")

    def test_usd_price_converted_in_normalize(self):
        rec = normalize("ebay", {**_raw(), "price": 100.0, "currency": "USD"})
        assert rec.price == round(100.0 * 0.92, 2)
        assert rec.currency == "EUR"


# ── Size normalisation ────────────────────────────────────────────────────────

class TestSizeNormalization:
    @pytest.mark.parametrize("raw,expected_eu", [
        ("XS", "XS"), ("S", "S"), ("M", "M"), ("L", "L"), ("XL", "XL"),
        ("XXL", "XXL"),
        ("42", "42"), ("38", "38"), ("36", "36"),
        ("EU 42", "42"), ("EU 38", "38"),
    ])
    def test_known_sizes(self, raw: str, expected_eu: str):
        _, size_eu = _normalize_size(raw)
        assert size_eu == expected_eu

    def test_none_returns_none_tuple(self):
        assert _normalize_size(None) == (None, None)

    def test_empty_returns_none_tuple(self):
        assert _normalize_size("") == (None, None)

    def test_unknown_size_preserves_raw(self):
        size_raw, size_eu = _normalize_size("ONESIZE")
        assert size_raw == "ONESIZE"
        assert size_eu is None

    def test_size_raw_preserved(self):
        size_raw, _ = _normalize_size("M")
        assert size_raw == "M"

    def test_normalize_sets_size_fields(self):
        rec = normalize("ebay", {**_raw(), "size_raw": "EU 42"})
        assert rec.size_raw == "EU 42"
        assert rec.size_eu == "42"


# ── Condition mapping ─────────────────────────────────────────────────────────

class TestConditionMapping:
    @pytest.mark.parametrize("raw,expected", [
        ("NEW", ProductCondition.new),
        ("LIKE_NEW", ProductCondition.like_new),
        ("VERY_GOOD", ProductCondition.like_new),
        ("GOOD", ProductCondition.good),
        ("USED", ProductCondition.good),
        ("ACCEPTABLE", ProductCondition.fair),
        ("FOR_PARTS_OR_NOT_WORKING", ProductCondition.fair),
        ("new", ProductCondition.new),
        ("like_new", ProductCondition.like_new),
        ("good", ProductCondition.good),
        ("fair", ProductCondition.fair),
        ("UNKNOWN_LABEL", ProductCondition.fair),
        (None, ProductCondition.good),
    ])
    def test_condition(self, raw, expected):
        assert _normalize_condition(raw) == expected


# ── Category mapping ──────────────────────────────────────────────────────────

class TestCategoryMapping:
    @pytest.mark.parametrize("cat_id,expected", [
        ("15709", "sneakers"),
        ("63889", "sneakers"),
        ("57988", "vestes"),
        ("11483", "jeans"),
        ("15689", "jeans"),
        ("15687", "tee-shirts"),
        ("169291", "accessoires"),
    ])
    def test_by_category_id(self, cat_id: str, expected: str):
        assert _normalize_category(cat_id, None, "") == expected

    @pytest.mark.parametrize("title,expected", [
        ("Nike Air Max baskets", "sneakers"),
        ("Veste The North Face", "vestes"),
        ("Jean slim bleu", "jeans"),
        ("Tee-shirt blanc Lacoste", "tee-shirts"),
        ("Sac à dos vintage", "accessoires"),
    ])
    def test_by_title_keyword(self, title: str, expected: str):
        assert _normalize_category(None, None, title) == expected

    def test_already_internal_category_preserved(self):
        assert _normalize_category(None, "sneakers", "") == "sneakers"

    def test_unknown_falls_back_to_accessoires(self):
        assert _normalize_category("9999", None, "objet mystère") == "accessoires"
