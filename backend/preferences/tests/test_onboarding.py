"""Tests for preferences.onboarding -- routes A & B (KAN-33, KAN-34).

Note: the ticket's own AC test description ("trois styles streetwear
selectionnes donnent un vecteur proche des produits streetwear du golden
catalogue") can't be built against evaluation/fixtures/golden_catalogue.json
as written -- that fixture has no style tags and no embeddings, only
category/brand/price. TestSelectedStylesAreCloserThanUnrelated below tests
the same underlying property (the averaged vector leans toward the styles
that were actually picked) using this module's own archetype catalogue.
Similarly, KAN-34's "three vintage-jacket photos land closer to 'vintage
jacket' than 'sneakers'" needs real photos and a real model to be literal;
TestImagesLeanTowardTheirOwnEncoding below tests the same property (the
averaged vector is closer to its own sources than to an unrelated one) with
a fake EmbeddingService, since the real model is never run in unit tests.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from preferences.onboarding import (
    ARCHETYPE_EMBEDDINGS,
    MAX_ONBOARDING_IMAGE_BYTES,
    MAX_ONBOARDING_IMAGES,
    STYLE_ARCHETYPE_IDS,
    build_profile_from_images,
    build_profile_from_styles,
)


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b)


class _FakeEmbeddingService:
    """Deterministic stand-in for FashionSigLIPService: maps known byte
    payloads to fixed vectors, and can be told to blow up on specific ones.
    """

    vector_dim = 4
    embedding_version = "fake-v1"

    def __init__(self, mapping: dict[bytes, list[float]], raise_for: set[bytes] | None = None):
        self._mapping = mapping
        self._raise_for = raise_for or set()

    def encode_image(self, image: bytes) -> np.ndarray:
        if image in self._raise_for:
            raise RuntimeError("model failure")
        return np.array(self._mapping[image], dtype=np.float32)

    def encode_text(self, text: str) -> np.ndarray:
        raise NotImplementedError


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


class TestImagesEmptyInput:
    def test_returns_valid_cold_start_profile(self) -> None:
        profile = build_profile_from_images([], _FakeEmbeddingService({}))
        assert profile.is_cold_start is True
        assert profile.vectors.positive == []


class TestImagesTooMany:
    def test_more_than_max_raises(self, tmp_path) -> None:
        paths = []
        for i in range(MAX_ONBOARDING_IMAGES + 1):
            p = tmp_path / f"img{i}.jpg"
            p.write_bytes(b"x")
            paths.append(str(p))

        with pytest.raises(ValueError):
            build_profile_from_images(paths, _FakeEmbeddingService({}))


class TestImagesSingle:
    def test_returns_that_images_own_normalized_encoding(self, tmp_path) -> None:
        p = tmp_path / "a.jpg"
        p.write_bytes(b"photo-a")
        service = _FakeEmbeddingService({b"photo-a": [3.0, 0.0, 0.0, 0.0]})

        profile = build_profile_from_images([str(p)], service)

        assert profile.vectors.positive == pytest.approx([1.0, 0.0, 0.0, 0.0])


class TestImagesMultiple:
    def test_returns_normalized_average(self, tmp_path) -> None:
        p1, p2 = tmp_path / "a.jpg", tmp_path / "b.jpg"
        p1.write_bytes(b"photo-a")
        p2.write_bytes(b"photo-b")
        service = _FakeEmbeddingService(
            {b"photo-a": [1.0, 0.0, 0.0, 0.0], b"photo-b": [0.0, 1.0, 0.0, 0.0]},
        )

        profile = build_profile_from_images([str(p1), str(p2)], service)

        norm = math.sqrt(2) / 2
        assert profile.vectors.positive == pytest.approx([norm, norm, 0.0, 0.0])


class TestImagesOversizedSkipped:
    def test_oversized_image_is_skipped_others_still_used(self, tmp_path) -> None:
        small = tmp_path / "small.jpg"
        small.write_bytes(b"photo-a")
        big = tmp_path / "big.jpg"
        big.write_bytes(b"x" * (MAX_ONBOARDING_IMAGE_BYTES + 1))
        service = _FakeEmbeddingService({b"photo-a": [1.0, 0.0, 0.0, 0.0]})

        profile = build_profile_from_images([str(small), str(big)], service)

        assert profile.vectors.positive == pytest.approx([1.0, 0.0, 0.0, 0.0])


class TestImagesUnreadablePathSkipped:
    def test_nonexistent_path_is_skipped(self, tmp_path) -> None:
        real = tmp_path / "a.jpg"
        real.write_bytes(b"photo-a")
        missing = str(tmp_path / "does-not-exist.jpg")
        service = _FakeEmbeddingService({b"photo-a": [1.0, 0.0, 0.0, 0.0]})

        profile = build_profile_from_images([str(real), missing], service)

        assert profile.vectors.positive == pytest.approx([1.0, 0.0, 0.0, 0.0])


class TestImagesEncodeFailureSkipped:
    def test_model_failure_on_one_image_does_not_crash_onboarding(self, tmp_path) -> None:
        good = tmp_path / "good.jpg"
        good.write_bytes(b"photo-a")
        bad = tmp_path / "bad.jpg"
        bad.write_bytes(b"photo-bad")
        service = _FakeEmbeddingService(
            {b"photo-a": [1.0, 0.0, 0.0, 0.0]},
            raise_for={b"photo-bad"},
        )

        profile = build_profile_from_images([str(good), str(bad)], service)

        assert profile.vectors.positive == pytest.approx([1.0, 0.0, 0.0, 0.0])


class TestImagesAllInvalidReturnsColdStart:
    def test_all_unreadable_returns_cold_start(self, tmp_path) -> None:
        missing = str(tmp_path / "does-not-exist.jpg")
        profile = build_profile_from_images([missing], _FakeEmbeddingService({}))
        assert profile.is_cold_start is True


class TestImagesLeanTowardTheirOwnEncoding:
    def test_averaged_vector_closer_to_sources_than_to_unrelated(self, tmp_path) -> None:
        """Stand-in for the ticket's own AC ('three vintage-jacket photos
        land closer to "vintage jacket" than "sneakers"'): the profile built
        from a set of images must be more similar to each source image's own
        encoding than to an unrelated encoding -- checked with a fake
        embedding service since the real model isn't run in unit tests.
        """
        vectors = {
            b"photo-0": [1.0, 0.2, 0.0, 0.0],
            b"photo-1": [0.9, 0.3, 0.1, 0.0],
            b"photo-2": [0.95, 0.1, 0.05, 0.0],
        }
        paths = []
        for content in vectors:
            p = tmp_path / f"{content.decode()}.jpg"
            p.write_bytes(content)
            paths.append(str(p))
        service = _FakeEmbeddingService(vectors)

        profile = build_profile_from_images(paths, service)
        result_vector = profile.vectors.positive

        similarity_to_sources = min(
            _cosine(result_vector, vectors[key]) for key in vectors
        )
        similarity_to_unrelated = _cosine(result_vector, [0.0, 0.0, 0.0, 1.0])

        assert similarity_to_sources > similarity_to_unrelated
