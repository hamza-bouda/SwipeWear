"""EmbeddingService protocol — swappable adapter for image/text embedding models."""
from __future__ import annotations

from typing import Protocol

import numpy as np

EMBEDDING_VERSION = "fashionsiglip-v1"
VECTOR_DIM = 768


class EmbeddingService(Protocol):
    """Adapter contract for embedding models.

    Both methods return a (768,) float32 L2-normalised vector.
    Concrete implementations: FashionSigLIPService (KAN-28).
    Swap candidates: Qwen3-VL-Embedding (KAN-30 bench).
    """

    embedding_version: str
    vector_dim: int

    def encode_image(self, image: bytes) -> np.ndarray:
        """Encode image bytes → (vector_dim,) float32 L2-normalised vector."""
        ...

    def encode_text(self, text: str) -> np.ndarray:
        """Encode text → (vector_dim,) float32 L2-normalised vector, same space as encode_image."""
        ...
