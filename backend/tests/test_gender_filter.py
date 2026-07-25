"""Tests for gender inference and filtering — KAN-88.

The feed mixed menswear and womenswear with no way to say which you wanted, so
roughly half of every deck was irrelevant to the shopper.
"""
from __future__ import annotations

import pytest

from contracts.product import (
    Gender, ProductCondition, ProductRecord, ProductSource,
)
from contracts.profile import HardConstraints
from ingestion.normalizer import infer_gender
from retrieval.filters import apply_hard_filters, matches_hard_filters


class _Profile:
    def __init__(self, **kwargs):
        self.hard_constraints = HardConstraints(**kwargs)


def _product(gender: str | None) -> ProductRecord:
    return ProductRecord(
        id="p1",
        source=ProductSource.ebay,
        source_record_id="1",
        title="Veste",
        price=50.0,
        condition=ProductCondition.good,
        category="vestes",
        image_urls=["https://example.com/i.jpg"],
        gender=gender,
    )


class TestInference:
    @pytest.mark.parametrize("title, expected", [
        ("Veste Nike Homme Taille L", "men"),
        ("Pull pour hommes", "men"),
        ("Robe Calvin Klein Femme", "women"),
        ("Chaussures pour dames", "women"),
        ("Sweat unisexe Champion", "unisex"),
        ("Veste mixte", "unisex"),
    ])
    def test_french_titles(self, title, expected):
        assert infer_gender(title) == expected

    @pytest.mark.parametrize("title, expected", [
        ("Nike Women's Air Max", "women"),
        ("Ladies Jacket", "women"),
        ("Men's Carhartt Jacket", "men"),
        ("Boys T-Shirt", "men"),
    ])
    def test_english_titles(self, title, expected):
        """'women' contains 'men' — a substring test files every women's
        listing under menswear, so women is matched first on word boundaries."""
        assert infer_gender(title) == expected

    def test_both_genders_named_means_unisex(self):
        assert infer_gender("Veste homme ou femme") == "unisex"

    def test_silence_is_not_a_guess(self):
        """Inventing a gender would hide the item from whoever it belongs to."""
        assert infer_gender("Nike Air Max 90") is None
        assert infer_gender("") is None

    def test_a_brand_containing_man_is_not_menswear(self):
        assert infer_gender("Sac Longchamp") is None

    @pytest.mark.parametrize("category_id, expected", [
        ("15709", "men"),    # Chaussures homme
        ("63889", "women"),  # Chaussures femme
    ])
    def test_category_id_wins_over_a_silent_title(self, category_id, expected):
        assert infer_gender("Baskets", category_id) == expected


class TestSqlFilter:
    def test_no_preference_adds_no_clause(self):
        result = apply_hard_filters(_Profile())
        assert "gender" not in result.applied

    def test_preference_adds_a_clause(self):
        result = apply_hard_filters(_Profile(gender=Gender.women))
        assert "gender" in result.applied
        assert any("gender" in c for c in result.clauses)

    def test_unisex_is_always_included(self):
        """A unisex item suits anybody and belongs in every feed."""
        result = apply_hard_filters(_Profile(gender=Gender.men))
        assert "unisex" in result.params["filter_genders"]
        assert "men" in result.params["filter_genders"]
        assert "women" not in result.params["filter_genders"]

    def test_unrecorded_gender_is_kept(self):
        """22 443 of 50 927 products state no gender; excluding them would
        throw away nearly half the catalogue."""
        result = apply_hard_filters(_Profile(gender=Gender.women))
        clause = next(c for c in result.clauses if "gender" in c)
        assert "IS NULL" in clause


class TestInMemoryFilter:
    """Must agree with the SQL clause or the two paths disagree."""

    def test_matching_gender_passes(self):
        assert matches_hard_filters(
            _product("women"), HardConstraints(gender=Gender.women),
        )

    def test_unisex_passes_for_everyone(self):
        for wanted in (Gender.men, Gender.women):
            assert matches_hard_filters(
                _product("unisex"), HardConstraints(gender=wanted),
            )

    def test_unrecorded_gender_passes(self):
        assert matches_hard_filters(
            _product(None), HardConstraints(gender=Gender.men),
        )

    def test_opposite_gender_is_rejected(self):
        assert not matches_hard_filters(
            _product("men"), HardConstraints(gender=Gender.women),
        )

    def test_no_preference_accepts_everything(self):
        for gender in ("men", "women", "unisex", None):
            assert matches_hard_filters(_product(gender), HardConstraints())
