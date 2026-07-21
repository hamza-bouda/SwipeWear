"""Optional slow KAN-67 acceptance test using the real quantized Qwen model."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from vision.qwen import (
    GARMENT_CATEGORIES,
    Qwen3VLRunner,
    QwenSceneAnalyzer,
)

RUN_REAL_QWEN = os.getenv("RUN_REAL_QWEN_ACCEPTANCE") == "1"
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
ACCEPTANCE_IMAGES = tuple(
    name.strip()
    for name in os.getenv(
        "QWEN_ACCEPTANCE_IMAGES",
        "woman.jpg,shop.jpg,rack.jpg",
    ).split(",")
    if name.strip()
)


@pytest.mark.skipif(
    not RUN_REAL_QWEN,
    reason="set RUN_REAL_QWEN_ACCEPTANCE=1 for the slow CPU acceptance run",
)
def test_real_qwen_detects_two_garments_per_fashion_scene() -> None:
    analyzer = QwenSceneAnalyzer(Qwen3VLRunner(max_new_tokens=256))

    for image_name in ACCEPTANCE_IMAGES:
        image = (
            REPOSITORY_ROOT / "tests_ia" / "images" / image_name
        ).read_bytes()
        result = analyzer.analyze(image)

        assert result.fallback_used is False, (
            f"{image_name}: {result.fallback_reason}"
        )
        assert len(result.garments) >= 2, image_name
        assert len(result.garment_crops) >= 2, image_name
        assert all(
            garment.category in GARMENT_CATEGORIES
            for garment in result.garments
        ), image_name
        print(
            f"accepted {image_name}: "
            f"{[garment.category for garment in result.garments]}",
            flush=True,
        )
