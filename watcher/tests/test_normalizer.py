"""Tests for watcher/normalizer.py (KAN-72)."""
from __future__ import annotations

import pytest

from watcher.models import VintedListing
from watcher.normalizer import _CONDITION_MAP, _stable_id, normalise


class TestStableId:
    def test_deterministic(self):
        assert _stable_id("abc") == _stable_id("abc")

    def test_different_ids_differ(self):
        assert _stable_id("abc") != _stable_id("xyz")

    def test_prefixed_with_vinted(self):
        assert _stable_id("123").startswith("vinted-")


class TestNormalise:
    def _listing(self, **kwargs) -> VintedListing:
        defaults = dict(
            listing_id="42",
            title="  Nike Air Max 90  ",
            price_eur=45.0,
            condition="good",
            size_label="42",
            brand="Nike",
            category="shoes",
            image_urls=["https://cdn.vinted.fr/img/1.jpg"],
            listing_url="https://www.vinted.fr/items/42",
        )
        defaults.update(kwargs)
        return VintedListing(**defaults)

    def test_source_is_vinted(self):
        row = normalise(self._listing())
        assert row["source"] == "vinted"

    def test_title_stripped(self):
        row = normalise(self._listing(title="  Jordan 1  "))
        assert row["title"] == "Jordan 1"

    def test_condition_mapped(self):
        for vinted_cond, expected in _CONDITION_MAP.items():
            row = normalise(self._listing(condition=vinted_cond))
            assert row["condition"] == expected

    def test_unknown_condition_defaults_to_good(self):
        row = normalise(self._listing(condition="unknown_value"))
        assert row["condition"] == "good"

    def test_raises_when_no_images(self):
        with pytest.raises(ValueError, match="no images"):
            normalise(self._listing(image_urls=[]))

    def test_id_stable_and_unique(self):
        r1 = normalise(self._listing(listing_id="1"))
        r2 = normalise(self._listing(listing_id="2"))
        assert r1["id"] != r2["id"]
        assert normalise(self._listing(listing_id="1"))["id"] == r1["id"]

    def test_no_personal_data_fields(self):
        row = normalise(self._listing())
        forbidden = {"seller_id", "seller_name", "seller_rating", "seller_location"}
        assert not forbidden.intersection(row.keys())

    def test_affiliate_url_is_listing_url(self):
        row = normalise(self._listing(listing_url="https://www.vinted.fr/items/99"))
        assert row["affiliate_url"] == "https://www.vinted.fr/items/99"
