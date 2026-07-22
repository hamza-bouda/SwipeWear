"""FashionSigLIP embedding adapter via OpenCLIP.

Model  : Marqo/marqo-fashionSigLIP (hf-hub)
Output : (768,) float32, L2-normalised (KAN-77: corrected from an
         unvalidated 512 assumption -- this is the model's real output dim)
Latency: < 350 ms/image on CPU (spec-validated: 284 ms)
"""
from __future__ import annotations

import logging
import os
from io import BytesIO
from typing import Any

import numpy as np

from embeddings.interfaces import EMBEDDING_VERSION, VECTOR_DIM

_LOG = logging.getLogger("swipewear.embeddings.fashionsiglip")

_HF_REPO = os.getenv("FASHIONSIGLIP_MODEL", "hf-hub:Marqo/marqo-fashionSigLIP")

# Module-level singletons — loaded once, never reloaded per request.
_model: Any = None
_preprocess: Any = None
_tokenizer: Any = None


def _load() -> tuple[Any, Any, Any]:
    """Load model exactly once; subsequent calls return the cached objects."""
    global _model, _preprocess, _tokenizer
    if _model is None:
        import open_clip  # type: ignore[import]

        _model, _, _preprocess = open_clip.create_model_and_transforms(_HF_REPO)
        _tokenizer = open_clip.get_tokenizer(_HF_REPO)
        _model.eval()
        _LOG.info(
            "FashionSigLIP loaded: %s  dim=%d",
            _HF_REPO,
            VECTOR_DIM,
            extra={"pipe_module": "embeddings.fashionsiglip"},
        )
    return _model, _preprocess, _tokenizer


def _run_image(image_bytes: bytes) -> np.ndarray:
    """Run the model on image bytes → raw (un-normalised) float32 vector."""
    import torch  # type: ignore[import]
    from PIL import Image  # type: ignore[import]

    model, preprocess, _ = _load()
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    tensor = preprocess(img).unsqueeze(0)
    with torch.no_grad():
        feats = model.encode_image(tensor)
    return feats.squeeze(0).cpu().numpy().astype(np.float32)


def _run_text(text: str) -> np.ndarray:
    """Run the model on a text string → raw (un-normalised) float32 vector."""
    import torch  # type: ignore[import]

    model, _, tokenizer = _load()
    tokens = tokenizer([text])
    with torch.no_grad():
        feats = model.encode_text(tokens)
    return feats.squeeze(0).cpu().numpy().astype(np.float32)


def _l2_normalize(v: np.ndarray) -> np.ndarray:
    """Return the L2-normalised vector; returns v unchanged if norm is zero."""
    norm = float(np.linalg.norm(v))
    if norm == 0.0:
        return v.astype(np.float32)
    return (v / norm).astype(np.float32)


class FashionSigLIPService:
    """Concrete EmbeddingService backed by Marqo-FashionSigLIP via OpenCLIP."""

    embedding_version: str = EMBEDDING_VERSION
    vector_dim: int = VECTOR_DIM

    def encode_image(self, image: bytes) -> np.ndarray:
        """Encode raw image bytes → (768,) float32 L2-normalised vector."""
        return _l2_normalize(_run_image(image))

    def encode_text(self, text: str) -> np.ndarray:
        """Encode text → (768,) float32 L2-normalised vector (same space as encode_image)."""
        return _l2_normalize(_run_text(text))


# ── Module-level singleton ───────────────────────────────────────────────────

_service: FashionSigLIPService | None = None


def get_service() -> FashionSigLIPService:
    """Return the process-wide FashionSigLIPService (model loaded on first call)."""
    global _service
    if _service is None:
        _service = FashionSigLIPService()
    return _service
