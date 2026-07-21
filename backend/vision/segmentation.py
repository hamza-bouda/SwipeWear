"""Optional SegFormer clothing isolation for worn catalogue photos."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from io import BytesIO
from typing import Any, Protocol

import numpy as np
from PIL import Image

MODEL_ID = "mattmdjaga/segformer_b2_clothes"

# Labels published by the model configuration.
GARMENT_LABEL_IDS = frozenset({1, 4, 5, 6, 7, 8, 9, 10, 17})
PERSON_LABEL_IDS = frozenset({2, 11, 12, 13, 14, 15})
MIN_PERSON_FRACTION = 0.001
_LOG = logging.getLogger("swipewear.vision.segmentation")
_default_runner: TransformersSegFormerRunner | None = None


class SemanticSegmenter(Protocol):
    """Boundary for semantic segmentation implementations."""

    model_id: str

    def segment(self, image: Image.Image) -> np.ndarray:
        """Return a height-by-width array of semantic label IDs."""
        ...


@dataclass(frozen=True)
class IsolationResult:
    """Observable result used by evaluation and the safe bytes-only wrapper."""

    image: bytes
    applied: bool
    person_detected: bool
    garment_fraction: float
    fallback_used: bool = False
    fallback_reason: str | None = None


class TransformersSegFormerRunner:
    """Lazy CPU SegFormer runner backed by Hugging Face Transformers."""

    model_id = MODEL_ID

    def __init__(self) -> None:
        self._processor: Any | None = None
        self._model: Any | None = None

    def _load(self) -> tuple[Any, Any]:
        if self._processor is None or self._model is None:
            from transformers import (
                AutoImageProcessor,
                SegformerForSemanticSegmentation,
            )

            self._processor = AutoImageProcessor.from_pretrained(self.model_id)
            self._model = SegformerForSemanticSegmentation.from_pretrained(
                self.model_id
            )
            self._model.eval()
        return self._processor, self._model

    def segment(self, image: Image.Image) -> np.ndarray:
        import torch

        processor, model = self._load()
        inputs = processor(images=image, return_tensors="pt")
        with torch.inference_mode():
            outputs = model(**inputs)
        height, width = image.height, image.width
        segmentation = processor.post_process_semantic_segmentation(
            outputs,
            target_sizes=[(height, width)],
        )[0]
        return segmentation.cpu().numpy().astype(np.int16, copy=False)


def isolate_garment(
    image: bytes,
    *,
    runner: SemanticSegmenter | None = None,
) -> bytes:
    """Return an isolated garment crop, or the original bytes on any fallback."""
    return isolate_garment_with_result(image, runner=runner).image


def isolate_garment_with_result(
    image: bytes,
    *,
    runner: SemanticSegmenter | None = None,
) -> IsolationResult:
    """Isolate clothing only when the semantic map contains a person."""
    try:
        source = Image.open(BytesIO(image)).convert("RGB")
        segmenter = runner or _get_default_runner()
        labels = np.asarray(segmenter.segment(source))
        expected_shape = (source.height, source.width)
        if labels.shape != expected_shape:
            raise ValueError(
                f"expected segmentation shape {expected_shape}, got {labels.shape}"
            )

        person_mask = np.isin(labels, tuple(PERSON_LABEL_IDS))
        person_pixels = int(person_mask.sum())
        required_person_pixels = max(
            1,
            int(labels.size * MIN_PERSON_FRACTION),
        )
        if person_pixels < required_person_pixels:
            return IsolationResult(
                image=image,
                applied=False,
                person_detected=False,
                garment_fraction=0.0,
            )

        garment_mask = np.isin(labels, tuple(GARMENT_LABEL_IDS))
        garment_pixels = int(garment_mask.sum())
        if garment_pixels == 0:
            return IsolationResult(
                image=image,
                applied=False,
                person_detected=True,
                garment_fraction=0.0,
                fallback_used=True,
                fallback_reason="person detected but no garment mask found",
            )

        isolated = _masked_crop(source, garment_mask)
        return IsolationResult(
            image=isolated,
            applied=True,
            person_detected=True,
            garment_fraction=garment_pixels / labels.size,
        )
    except Exception as exc:  # noqa: BLE001 - original-image fallback is mandatory
        _LOG.exception(
            "Garment segmentation failed; using original image",
            extra={
                "pipe_module": "vision.segmentation",
                "fallback_used": True,
            },
        )
        return IsolationResult(
            image=image,
            applied=False,
            person_detected=False,
            garment_fraction=0.0,
            fallback_used=True,
            fallback_reason=f"{type(exc).__name__}: {exc}",
        )


def _get_default_runner() -> TransformersSegFormerRunner:
    global _default_runner
    if _default_runner is None:
        _default_runner = TransformersSegFormerRunner()
    return _default_runner


def _masked_crop(source: Image.Image, mask: np.ndarray) -> bytes:
    ys, xs = np.nonzero(mask)
    left, right = int(xs.min()), int(xs.max()) + 1
    top, bottom = int(ys.min()), int(ys.max()) + 1
    padding = max(1, round(max(source.size) * 0.03))
    left = max(0, left - padding)
    top = max(0, top - padding)
    right = min(source.width, right + padding)
    bottom = min(source.height, bottom + padding)

    pixels = np.asarray(source).copy()
    pixels[~mask] = 255
    cropped = Image.fromarray(pixels, mode="RGB").crop(
        (left, top, right, bottom)
    )
    output = BytesIO()
    cropped.save(output, format="PNG")
    return output.getvalue()
