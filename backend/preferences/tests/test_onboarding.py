"""Tests for preferences.onboarding -- route A, style grid (KAN-33).

Note: the ticket's own AC test description ("trois styles streetwear
selectionnes donnent un vecteur proche des produits streetwear du golden
catalogue") can't be built against evaluation/fixtures/golden_catalogue.json
as written -- that fixture has no style tags and no embeddings, only
category/brand/price. TestSelectedStylesAreCloserThanUnrelated below tests
the same underlying property (the averaged vector leans toward the styles
that were actually picked) using this module's own archetype catalogue.
"""
from __future__ import annotations

import math

import pytest

from preferences.onboarding import (
    ARCHETYPE_EMBEDDINGS,
    STYLE_ARCHETYPE_IDS,
    build_profile_from_styles,
)


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b)


class TestCatalogue:
    def test_between_8_and_12_archetypes(self) -> None:
        assert 8 <= len(STYLE_ARCHETYPE_IDS) <= 12

    def test_every_archetype_has_a_768_dim_embedding(self) -> None:
        for style_id in STYLE_ARCHETYPE_IDS:
            assert len(ARCHETYPE_EMBEDDINGS[style_id]) == 768

    def test_embeddings_are_l2_normalized(self) -> None:
        for style_id in STYLE_ARCHETYPE_IDS:
            norm = math.sqrt(sum(v * v for v in ARCHETYPE_EMBEDDINGS[style_id]))
            assert norm == pytest.approx(1.0)


class TestEmptySelection:
    def test_returns_valid_cold_start_profile(self) -> None:
        profile = build_profile_from_styles([])
        assert profile.is_cold_start is True
        assert profile.vectors.positive == []

    def test_all_unknown_ids_also_returns_cold_start(self) -> None:
        profile = build_profile_from_styles(["not-a-real-style"])
        assert profile.is_cold_start is True


class TestSingleStyle:
    def test_returns_that_archetypes_own_embedding(self) -> None:
        profile = build_profile_from_styles(["streetwear"])
        assert profile.vectors.positive == pytest.approx(
            ARCHETYPE_EMBEDDINGS["streetwear"],
        )

    def test_resulting_vector_is_l2_normalized(self) -> None:
        profile = build_profile_from_styles(["vintage"])
        norm = math.sqrt(sum(v * v for v in profile.vectors.positive))
        assert norm == pytest.approx(1.0)


class TestMultipleStyles:
    def test_returns_normalized_average(self) -> None:
        selected = ["streetwear", "techwear", "casual"]
        profile = build_profile_from_styles(selected)

        dim = 768
        raw_avg = [
            sum(ARCHETYPE_EMBEDDINGS[s][i] for s in selected) / len(selected)
            for i in range(dim)
        ]
        norm = math.sqrt(sum(v * v for v in raw_avg))
        expected = [v / norm for v in raw_avg]

        assert profile.vectors.positive == pytest.approx(expected)

    def test_unknown_id_mixed_in_is_ignored(self) -> None:
        with_unknown = build_profile_from_styles(
            ["streetwear", "casual", "not-a-real-style"],
        )
        without_unknown = build_profile_from_styles(["streetwear", "casual"])
        assert with_unknown.vectors.positive == pytest.approx(
            without_unknown.vectors.positive,
        )


class TestSelectedStylesAreCloserThanUnrelated:
    def test_averaged_vector_leans_toward_the_picked_styles(self) -> None:
        """AC's intent: the resulting vector is "close to" what was picked.

        Three street-style-adjacent archetypes are averaged; the result
        must be more similar (cosine) to each of the three picked styles
        than to an archetype that wasn't picked at all.
        """
        picked = ["streetwear", "techwear", "casual"]
        profile = build_profile_from_styles(picked)
        result_vector = profile.vectors.positive

        similarity_to_picked = min(
            _cosine(result_vector, ARCHETYPE_EMBEDDINGS[s]) for s in picked
        )
        similarity_to_unrelated = _cosine(
            result_vector, ARCHETYPE_EMBEDDINGS["bohemian"],
        )

        assert similarity_to_picked > similarity_to_unrelated
