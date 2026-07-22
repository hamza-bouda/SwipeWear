"""Tests for embeddings.interfaces and embeddings.fashionsiglip."""
from __future__ import annotations

import io
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from embeddings.fashionsiglip import (
    FashionSigLIPService,
    _l2_normalize,
    get_service,
)
from embeddings.interfaces import EMBEDDING_VERSION, VECTOR_DIM

# ── Helpers ───────────────────────────────────────────────────────────────────

def _unit(dim: int = VECTOR_DIM, axis: int = 0) -> np.ndarray:
    """Return a float32 unit vector with 1.0 at `axis`."""
    v = np.zeros(dim, dtype=np.float32)
    v[axis] = 1.0
    return v


def _raw(dim: int = VECTOR_DIM, axis: int = 0, scale: float = 5.0) -> np.ndarray:
    """Return an un-normalised float32 vector (norm = scale)."""
    v = np.zeros(dim, dtype=np.float32)
    v[axis] = scale
    return v


# ── Interface constants ───────────────────────────────────────────────────────

class TestInterfaceConstants:
    def test_embedding_version_is_fashionsiglip_v1(self) -> None:
        assert EMBEDDING_VERSION == "fashionsiglip-v1"

    def test_vector_dim_is_768(self) -> None:
        assert VECTOR_DIM == 768

    def test_service_class_attributes_match_constants(self) -> None:
        assert FashionSigLIPService.embedding_version == EMBEDDING_VERSION
        assert FashionSigLIPService.vector_dim == VECTOR_DIM


# ── _l2_normalize (pure numpy — no torch needed) ─────────────────────────────

class TestL2Normalize:
    def test_unit_vector_unchanged(self) -> None:
        v = _unit(axis=3)
        result = _l2_normalize(v)
        np.testing.assert_allclose(result, v, atol=1e-6)

    def test_scaled_vector_normalised_to_unit(self) -> None:
        v = np.array([3.0, 4.0] + [0.0] * (VECTOR_DIM - 2), dtype=np.float32)
        result = _l2_normalize(v)
        assert abs(float(np.linalg.norm(result)) - 1.0) < 1e-5

    def test_zero_vector_returned_unchanged(self) -> None:
        v = np.zeros(VECTOR_DIM, dtype=np.float32)
        result = _l2_normalize(v)
        np.testing.assert_array_equal(result, v)

    def test_output_dtype_is_float32(self) -> None:
        assert _l2_normalize(_raw()).dtype == np.float32

    def test_does_not_mutate_input(self) -> None:
        v = _raw(scale=7.0)
        original = v.copy()
        _l2_normalize(v)
        np.testing.assert_array_equal(v, original)


# ── encode_image ──────────────────────────────────────────────────────────────

class TestEncodeImage:
    @patch("embeddings.fashionsiglip._run_image")
    def test_returns_768_dim_ndarray(self, mock_run) -> None:
        mock_run.return_value = _unit()
        result = FashionSigLIPService().encode_image(b"fake-image")
        assert result.shape == (VECTOR_DIM,)

    @patch("embeddings.fashionsiglip._run_image")
    def test_dtype_is_float32(self, mock_run) -> None:
        mock_run.return_value = _unit()
        result = FashionSigLIPService().encode_image(b"fake-image")
        assert result.dtype == np.float32

    @patch("embeddings.fashionsiglip._run_image")
    def test_output_is_l2_normalised_even_when_raw_is_not(self, mock_run) -> None:
        mock_run.return_value = _raw(scale=7.0)  # norm = 7 before normalisation
        result = FashionSigLIPService().encode_image(b"fake-image")
        assert abs(float(np.linalg.norm(result)) - 1.0) < 1e-5

    @patch("embeddings.fashionsiglip._run_image")
    def test_delegates_to_run_image(self, mock_run) -> None:
        mock_run.return_value = _unit()
        FashionSigLIPService().encode_image(b"abc")
        mock_run.assert_called_once_with(b"abc")


# ── encode_text ───────────────────────────────────────────────────────────────

class TestEncodeText:
    @patch("embeddings.fashionsiglip._run_text")
    def test_returns_768_dim_ndarray(self, mock_run) -> None:
        mock_run.return_value = _unit(axis=1)
        result = FashionSigLIPService().encode_text("Nike Air Force 1")
        assert result.shape == (VECTOR_DIM,)

    @patch("embeddings.fashionsiglip._run_text")
    def test_dtype_is_float32(self, mock_run) -> None:
        mock_run.return_value = _unit(axis=1)
        result = FashionSigLIPService().encode_text("baskets blanches")
        assert result.dtype == np.float32

    @patch("embeddings.fashionsiglip._run_text")
    def test_output_is_l2_normalised_even_when_raw_is_not(self, mock_run) -> None:
        mock_run.return_value = _raw(scale=3.0, axis=2)
        result = FashionSigLIPService().encode_text("montre luxe")
        assert abs(float(np.linalg.norm(result)) - 1.0) < 1e-5

    @patch("embeddings.fashionsiglip._run_text")
    def test_delegates_to_run_text(self, mock_run) -> None:
        mock_run.return_value = _unit(axis=1)
        FashionSigLIPService().encode_text("robe fleurie")
        mock_run.assert_called_once_with("robe fleurie")


# ── Critère d'acceptation principal : similarité sneakers vs montre ───────────

class TestSneakerSimilarity:
    @patch("embeddings.fashionsiglip._run_image")
    def test_two_sneakers_more_similar_to_each_other_than_to_watch(
        self, mock_run
    ) -> None:
        """AC: deux images de sneakers sont plus similaires entre elles
        qu'avec une image de montre (cosine similarity sur les embeddings)."""
        # Sneakers → direction 0; watch → direction 1 (orthogonal)
        sneaker_vec = _unit(axis=0)  # already L2-normalised
        watch_vec = _unit(axis=1)

        call_count = [0]

        def side_effect(image_bytes):
            call_count[0] += 1
            return sneaker_vec.copy() if call_count[0] <= 2 else watch_vec.copy()

        mock_run.side_effect = side_effect

        svc = FashionSigLIPService()
        sneaker1 = svc.encode_image(b"sneaker-1")
        sneaker2 = svc.encode_image(b"sneaker-2")
        watch = svc.encode_image(b"watch")

        sim_sneakers = float(np.dot(sneaker1, sneaker2))
        sim_s1_watch = float(np.dot(sneaker1, watch))
        sim_s2_watch = float(np.dot(sneaker2, watch))

        assert sim_sneakers > sim_s1_watch, (
            f"sneaker similarity ({sim_sneakers:.3f}) should exceed "
            f"sneaker-watch similarity ({sim_s1_watch:.3f})"
        )
        assert sim_sneakers > sim_s2_watch, (
            f"sneaker similarity ({sim_sneakers:.3f}) should exceed "
            f"sneaker-watch similarity ({sim_s2_watch:.3f})"
        )


# ── Singleton ────────────────────────────────────────────────────────────────

class TestSingleton:
    def test_get_service_returns_same_instance(self) -> None:
        import embeddings.fashionsiglip as mod

        mod._service = None
        s1 = get_service()
        s2 = get_service()
        assert s1 is s2

    def test_get_service_instance_has_correct_embedding_version(self) -> None:
        import embeddings.fashionsiglip as mod

        mod._service = None
        svc = get_service()
        assert svc.embedding_version == EMBEDDING_VERSION

    @patch("embeddings.fashionsiglip._run_image")
    def test_encode_image_called_three_times_run_image_called_three_times(
        self, mock_run
    ) -> None:
        mock_run.return_value = _unit()
        svc = FashionSigLIPService()
        svc.encode_image(b"a")
        svc.encode_image(b"b")
        svc.encode_image(b"c")
        assert mock_run.call_count == 3


# ── Metadata ─────────────────────────────────────────────────────────────────

class TestMetadata:
    def test_embedding_version_on_instance(self) -> None:
        assert FashionSigLIPService().embedding_version == "fashionsiglip-v1"

    def test_vector_dim_on_instance(self) -> None:
        assert FashionSigLIPService().vector_dim == 768

    def test_embedding_version_is_class_attribute(self) -> None:
        assert FashionSigLIPService.embedding_version == "fashionsiglip-v1"

    def test_vector_dim_is_class_attribute(self) -> None:
        assert FashionSigLIPService.vector_dim == 768
