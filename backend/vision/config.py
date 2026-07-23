"""Configurable thresholds for vision modules."""
from __future__ import annotations

import os

# DINOv2 cosine similarity threshold for "same item" (exact match).
# Validated: same item ~0.956, same style ~0.508, unrelated ~0.074.
# Margin of 0.448 — threshold 0.80 leaves comfortable headroom.
# Will be recalibrated once real listing photos (cluttered backgrounds,
# amateur photography) are available.
DINOV2_EXACT_THRESHOLD: float = float(
    os.getenv("DINOV2_EXACT_THRESHOLD", "0.80")
)

# FashionSigLIP cosine similarity threshold for "similar style" tier.
FASHION_SIMILAR_THRESHOLD: float = float(
    os.getenv("FASHION_SIMILAR_THRESHOLD", "0.55")
)

# DINOv2 model name (HuggingFace Hub).
DINOV2_MODEL_NAME: str = os.getenv("DINOV2_MODEL", "facebook/dinov2-base")

# Target image size for DINOv2 preprocessing (square crop).
DINOV2_IMAGE_SIZE: int = 224
