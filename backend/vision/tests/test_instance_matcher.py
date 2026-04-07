"""Tests for vision/instance_matcher.py (KAN-70).

DINOv2 model is mocked — tests validate business logic (threshold routing,
cosine calculation, MatchTier assignment) without loading any real model.
"""
from __future__ import annotations

import math
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from vision.instance_matcher import MatchTier, MatchResult, _cosine, match


class TestCosine:
    def test_identical_vectors(self):
        v = [1.0, 0.0, 0.0]
        assert abs(_cosine(v, v) - 1.0) < 1e-6

    def test_orthogonal_vectors(self):
        assert abs(_cosine([1.0, 0.0], [0.0, 1.0])) < 1e-6

    def test_zero_vector(self):
        assert _cosine([0.0, 0.0], [1.0, 0.0]) == 0.0

    def test_l2_normalized_same_direction(self):
        s = 1 / math.sqrt(2)
        v = [s, s]
        assert abs(_cosine(v, v) - 1.0) < 1e-6


def _fake_encode(score: float):
    """Return a mock _encode_image that produces a vector yielding `score` cosine with reference."""
    def _encode(image_bytes: bytes) -> list[float]:
        return [score, 0.0, 0.0]
    return _encode


def _vec_at_cosine(target_cos: float) -> list[float]:
    """Return a 2-D unit vector whose cosine with [1,0] equals target_cos."""
    sin = math.sqrt(max(0.0, 1.0 - target_cos ** 2))
    return [target_cos, sin]


class TestMatch:
    def _reference(self) -> list[float]:
        return [1.0, 0.0]

    def test_exact_match_above_threshold(self):
        # cosine = 0.95 → above 0.80
        with patch("vision.instance_matcher._encode_image", return_value=_vec_at_cosine(0.95)):
            result = match(
                reference_dinov2_embedding=self._reference(),
                candidate_image=b"fake",
            )
        assert result.tier == MatchTier.exact
        assert result.dinov2_score >= 0.80

    def test_similar_match_with_fashion_above_threshold(self):
        # DINOv2 cosine = 0.50 (below 0.80) → not exact
        # Fashion cosine = 0.60 (above 0.55) → similar
        ref_fashion = [1.0, 0.0]
        cand_fashion = _vec_at_cosine(0.60)
        with patch("vision.instance_matcher._encode_image", return_value=_vec_at_cosine(0.50)):
            result = match(
                reference_dinov2_embedding=self._reference(),
                candidate_image=b"fake",
                reference_fashion_embedding=ref_fashion,
                candidate_fashion_embedding=cand_fashion,
            )
        assert result.tier == MatchTier.similar
        assert result.fashion_score is not None

    def test_no_match_low_scores(self):
        # DINOv2 cosine = 0.10, fashion cosine = 0.10 → no_match
        ref_fashion = [1.0, 0.0]
        cand_fashion = _vec_at_cosine(0.10)
        with patch("vision.instance_matcher._encode_image", return_value=_vec_at_cosine(0.10)):
            result = match(
                reference_dinov2_embedding=self._reference(),
                candidate_image=b"fake",
                reference_fashion_embedding=ref_fashion,
                candidate_fashion_embedding=cand_fashion,
            )
        assert result.tier == MatchTier.no_match

    def test_no_match_without_fashion_embeddings(self):
        # DINOv2 cosine = 0.50 (below exact threshold), no fashion → no_match
        with patch("vision.instance_matcher._encode_image", return_value=_vec_at_cosine(0.50)):
            result = match(
                reference_dinov2_embedding=self._reference(),
                candidate_image=b"fake",
            )
        assert result.tier == MatchTier.no_match
        assert result.fashion_score is None

    def test_exact_takes_priority_over_similar(self):
        # DINOv2 cosine = 0.99 → exact, regardless of fashion score
        with patch("vision.instance_matcher._encode_image", return_value=_vec_at_cosine(0.99)):
            result = match(
                reference_dinov2_embedding=self._reference(),
                candidate_image=b"fake",
                reference_fashion_embedding=[1.0, 0.0],
                candidate_fashion_embedding=_vec_at_cosine(0.90),
            )
        assert result.tier == MatchTier.exact

    def test_result_contains_dinov2_score(self):
        with patch("vision.instance_matcher._encode_image", return_value=_vec_at_cosine(0.90)):
            result = match(
                reference_dinov2_embedding=self._reference(),
                candidate_image=b"fake",
            )
        assert isinstance(result.dinov2_score, float)
        assert result.dinov2_score > 0


class TestAlertRunner:
    def test_no_alerts_returns_empty(self):
        from ingestion.alert_runner import evaluate_product_against_alerts
        conn = MagicMock()
        with patch("ingestion.alert_runner.fetch_active_specific_item_alerts", return_value=[]):
            result = evaluate_product_against_alerts(conn, b"fake_image")
        assert result == []

    def test_alert_without_dinov2_skipped(self):
        from ingestion.alert_runner import evaluate_product_against_alerts
        conn = MagicMock()
        rows = [(str(uuid4()), str(uuid4()), None, None)]
        with patch("ingestion.alert_runner.fetch_active_specific_item_alerts", return_value=rows):
            result = evaluate_product_against_alerts(conn, b"fake_image")
        assert result == []

    def test_exact_match_returned(self):
        from ingestion.alert_runner import evaluate_product_against_alerts
        aid = str(uuid4())
        uid = str(uuid4())
        dinov2_ref = [1.0, 0.0, 0.0]
        rows = [(aid, uid, dinov2_ref, None)]
        exact_result = MatchResult(tier=MatchTier.exact, dinov2_score=0.95)
        with patch("ingestion.alert_runner.fetch_active_specific_item_alerts", return_value=rows), \
             patch("ingestion.alert_runner.match", return_value=exact_result):
            matches = evaluate_product_against_alerts(conn=MagicMock(), product_image_bytes=b"img")
        assert len(matches) == 1
        assert matches[0].result.tier == MatchTier.exact

    def test_no_match_not_returned(self):
        from ingestion.alert_runner import evaluate_product_against_alerts
        aid = str(uuid4())
        uid = str(uuid4())
        dinov2_ref = [1.0, 0.0, 0.0]
        rows = [(aid, uid, dinov2_ref, None)]
        no_match = MatchResult(tier=MatchTier.no_match, dinov2_score=0.2)
        with patch("ingestion.alert_runner.fetch_active_specific_item_alerts", return_value=rows), \
             patch("ingestion.alert_runner.match", return_value=no_match):
            matches = evaluate_product_against_alerts(conn=MagicMock(), product_image_bytes=b"img")
        assert matches == []

    def test_match_failure_skipped_gracefully(self):
        from ingestion.alert_runner import evaluate_product_against_alerts
        aid = str(uuid4())
        uid = str(uuid4())
        dinov2_ref = [1.0, 0.0, 0.0]
        rows = [(aid, uid, dinov2_ref, None)]
        with patch("ingestion.alert_runner.fetch_active_specific_item_alerts", return_value=rows), \
             patch("ingestion.alert_runner.match", side_effect=RuntimeError("model error")):
            matches = evaluate_product_against_alerts(conn=MagicMock(), product_image_bytes=b"img")
        assert matches == []
