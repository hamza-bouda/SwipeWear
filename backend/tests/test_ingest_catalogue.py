"""Tests for the bulk catalogue ingestion plan — KAN-87.

The script itself talks to eBay and Postgres, so what is worth testing is the
two pure decisions it makes: which queries to run, in what order, and when a
brand may be attributed to an item.
"""
from __future__ import annotations

import pytest

from scripts.ingest_catalogue import (
    _BRANDS,
    _NOUNS,
    _attribute_brand,
    build_query_plan,
)


class TestQueryPlan:
    def test_plan_is_not_empty(self):
        assert build_query_plan()

    def test_queries_are_unique(self):
        queries = [q for _, q in build_query_plan()]
        assert len(queries) == len(set(queries))

    def test_every_category_is_represented(self):
        nouns = {q.rsplit(" ", 1)[-1] for _, q in build_query_plan()}
        for category_nouns in _NOUNS.values():
            assert nouns & set(category_nouns)

    def test_brand_is_a_prefix_of_its_query(self):
        for brand, query in build_query_plan():
            assert query.startswith(brand)

    def test_categories_are_interleaved_not_grouped(self):
        """A partial run must still cover all five categories.

        Grouping by category meant hitting --target left accessoires with a
        handful of items while sneakers took the entire budget.
        """
        first = [q.rsplit(" ", 1)[-1] for _, q in build_query_plan()[:len(_BRANDS)]]
        assert len(set(first)) == len(_BRANDS)


class TestBrandAttribution:
    def test_fills_brand_when_the_title_confirms_it(self):
        raw = {"title": "Nike Air Max 90 taille 42"}
        assert _attribute_brand(raw, "nike")["brand"] == "nike"

    def test_match_is_case_insensitive(self):
        raw = {"title": "THE NORTH FACE veste polaire"}
        assert _attribute_brand(raw, "the north face")["brand"] == "the north face"

    def test_leaves_brand_unset_when_the_title_disagrees(self):
        """'nike sneakers' also returns Adidas — attributing the search term
        blind would mislabel the catalogue."""
        raw = {"title": "Adidas Samba OG taille 43"}
        assert _attribute_brand(raw, "nike").get("brand") is None

    def test_never_overwrites_a_brand_the_source_supplied(self):
        raw = {"title": "Nike Air Max", "brand": "Nike Sportswear"}
        assert _attribute_brand(raw, "nike")["brand"] == "Nike Sportswear"

    @pytest.mark.parametrize("title", ["", None])
    def test_missing_title_is_not_an_error(self, title):
        assert _attribute_brand({"title": title}, "nike").get("brand") is None
