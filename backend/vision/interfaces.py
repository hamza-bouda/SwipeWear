"""Public contracts for replaceable scene-analysis adapters."""
from __future__ import annotations

import importlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, Field, model_validator

ImageTransform = Callable[[bytes], bytes]
DEFAULT_SEGMENTATION_REPORT = (
    Path(__file__).resolve().parents[1]
    / "evaluation"
    / "reports"
    / "segmentation_recall.json"
)

SCENE_SCHEMA_VERSION = 1


class GarmentBox(BaseModel):
    """Approximate garment bounds using normalized image coordinates."""

    x_min: float = Field(ge=0.0, le=1.0)
    y_min: float = Field(ge=0.0, le=1.0)
    x_max: float = Field(ge=0.0, le=1.0)
    y_max: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def bounds_have_positive_area(self) -> GarmentBox:
        if self.x_max <= self.x_min or self.y_max <= self.y_min:
            raise ValueError("garment box must have positive area")
        return self


class DetectedGarment(BaseModel):
    """Structured facts for one visible garment."""

    category: str = Field(min_length=1)
    colors: list[str] = Field(default_factory=list)
    style: str = Field(min_length=1)
    box: GarmentBox


class SceneAnalysis(BaseModel):
    """Validated scene facts and garment crops returned by SceneAnalyzer."""

    garments: list[DetectedGarment] = Field(default_factory=list)
    global_tags: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    garment_crops: list[bytes] = Field(default_factory=list, exclude=True)
    model: str = "qwen3-vl-2b-instruct"
    fallback_used: bool = False
    fallback_reason: str | None = None
    requires_tag_confirmation: bool = False
    schema_version: int = SCENE_SCHEMA_VERSION


class SceneAnalyzer(Protocol):
    """Swappable adapter contract for complex fashion-scene analysis."""

    def analyze(self, image: bytes) -> SceneAnalysis:
        """Analyze encoded image bytes and return validated structured facts."""
        ...


# Compatibility name kept for callers of the original placeholder interface.
SceneAnalysisResult = SceneAnalysis


async def analyze_scene(image_bytes: bytes) -> SceneAnalysisResult:
    """Compatibility placeholder for the original asynchronous API."""
    raise NotImplementedError


def get_active_image_transform(
    report_path: Path | None = None,
) -> ImageTransform | None:
    """Resolve garment isolation only after a strictly positive Recall@10 gain."""
    path = report_path or DEFAULT_SEGMENTATION_REPORT
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
        gain = float(report["recall_at_10"]["gain"])
        activated = bool(report["activated"])
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return None
    if not activated or gain <= 0.0:
        return None
    segmentation = importlib.import_module("vision.segmentation")
    transform = getattr(segmentation, "isolate_garment")
    return transform if callable(transform) else None
