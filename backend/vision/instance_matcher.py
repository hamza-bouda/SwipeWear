"""DINOv2-based instance matcher — distinguishes « same item » from « similar style ».

Validated thresholds (2026-07-16 tests):
    same item   : DINOv2 cosine ~0.956
    same style  : DINOv2 cosine ~0.508
    unrelated   : DINOv2 cosine ~0.074

`match()` is called by the ingestion alert runner (KAN-70).
It never runs per user-request — only during the product ingestion job.

CPU-only; DINOv2-base loads in ~600 ms on first call and is then cached.
Inference: ~150 ms/image on CPU (cls token extraction).
"""
from __future__ import annotations

import logging
import math
from enum import Enum
from io import BytesIO
from typing import Any

from pydantic import BaseModel

from vision.config import (
    DINOV2_EXACT_THRESHOLD,
    DINOV2_IMAGE_SIZE,
    DINOV2_MODEL_NAME,
    FASHION_SIMILAR_THRESHOLD,
)

_LOG = logging.getLogger("swipewear.vision.instance_matcher")

_model: Any = None
_processor: Any = None


def _load_dinov2() -> tuple[Any, Any]:
    global _model, _processor
    if _model is None:
        from transformers import AutoImageProcessor, AutoModel  # type: ignore[import]

        _LOG.info("Loading DINOv2 model: %s", DINOV2_MODEL_NAME)
        _processor = AutoImageProcessor.from_pretrained(DINOV2_MODEL_NAME)
        _model = AutoModel.from_pretrained(DINOV2_MODEL_NAME)
        _model.eval()
        _LOG.info("DINOv2 loaded (CPU, cls_token dim=768)")
    return _model, _processor


def _encode_image(image_bytes: bytes) -> list[float]:
    """Encode image bytes → DINOv2 CLS-token L2-normalised float32 vector."""
    import torch  # type: ignore[import]
    from PIL import Image  # type: ignore[import]

    model, processor = _load_dinov2()
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    inputs = processor(images=img, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
    cls = outputs.last_hidden_state[:, 0, :].squeeze(0).float()
    norm = cls.norm()
    if norm > 0:
        cls = cls / norm
    return cls.tolist()


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class MatchTier(str, Enum):
    exact = "exact"
    similar = "similar"
    no_match = "no_match"


class MatchResult(BaseModel):
    tier: MatchTier
    dinov2_score: float
    fashion_score: float | None = None
    threshold_used: float = DINOV2_EXACT_THRESHOLD


def match(
    reference_dinov2_embedding: list[float],
    candidate_image: bytes,
    reference_fashion_embedding: list[float] | None = None,
    candidate_fashion_embedding: list[float] | None = None,
) -> MatchResult:
    """Compare a new product image against a reference DINOv2 embedding.

    Args:
        reference_dinov2_embedding: L2-normalised DINOv2 CLS vector of the
            reference item (stored at alert creation).
        candidate_image: raw image bytes of the new product being evaluated.
        reference_fashion_embedding: FashionSigLIP vector of the alert reference
            (used for the "similar" tier fallback).
        candidate_fashion_embedding: FashionSigLIP vector of the candidate
            (pre-computed during ingestion; avoids double-encoding).

    Returns:
        MatchResult with tier (exact | similar | no_match) and scores.
    """
    candidate_dinov2 = _encode_image(candidate_image)
    dinov2_score = _cosine(reference_dinov2_embedding, candidate_dinov2)

    _LOG.debug("DINOv2 score=%.4f threshold=%.2f", dinov2_score, DINOV2_EXACT_THRESHOLD)

    if dinov2_score >= DINOV2_EXACT_THRESHOLD:
        return MatchResult(
            tier=MatchTier.exact,
            dinov2_score=dinov2_score,
        )

    fashion_score: float | None = None
    if reference_fashion_embedding is not None and candidate_fashion_embedding is not None:
        fashion_score = _cosine(reference_fashion_embedding, candidate_fashion_embedding)
        _LOG.debug("Fashion score=%.4f threshold=%.2f", fashion_score, FASHION_SIMILAR_THRESHOLD)
        if fashion_score >= FASHION_SIMILAR_THRESHOLD:
            return MatchResult(
                tier=MatchTier.similar,
                dinov2_score=dinov2_score,
                fashion_score=fashion_score,
            )

    return MatchResult(
        tier=MatchTier.no_match,
        dinov2_score=dinov2_score,
        fashion_score=fashion_score,
    )


def encode_reference(image_bytes: bytes) -> list[float]:
    """Compute and return the DINOv2 embedding for a reference item image.

    Call this at alert creation time (specific_item alerts) so the embedding
    can be cached and re-used by the alert runner without re-downloading.
    """
    return _encode_image(image_bytes)
