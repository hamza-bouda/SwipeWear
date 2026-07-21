from __future__ import annotations

import importlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

ImageTransform = Callable[[bytes], bytes]
DEFAULT_SEGMENTATION_REPORT = (
    Path(__file__).resolve().parents[1]
    / "evaluation"
    / "reports"
    / "segmentation_recall.json"
)


@dataclass
class SceneAnalysisResult:
    tags: list[str]
    garment_crops: list[bytes]
    model: str = "qwen3-vl-2b-instruct"
    fallback_used: bool = False


async def analyze_scene(image_bytes: bytes) -> SceneAnalysisResult:
    # Qwen on CPU; the embeddings module handles fallback to the whole image.
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
