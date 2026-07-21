from __future__ import annotations

import json
from io import BytesIO

import numpy as np
from PIL import Image

from vision.interfaces import get_active_image_transform
from vision.segmentation import (
    MODEL_ID,
    isolate_garment,
    isolate_garment_with_result,
)


def _image() -> bytes:
    output = BytesIO()
    Image.new("RGB", (20, 16), color=(20, 40, 60)).save(output, format="JPEG")
    return output.getvalue()


class FakeSegmenter:
    model_id = MODEL_ID

    def __init__(self, labels: np.ndarray | Exception) -> None:
        self.labels = labels

    def segment(self, image: Image.Image) -> np.ndarray:
        if isinstance(self.labels, Exception):
            raise self.labels
        return self.labels


def test_worn_garment_is_masked_and_cropped() -> None:
    labels = np.zeros((16, 20), dtype=np.int16)
    labels[1:4, 8:12] = 11  # face proves a person is present
    labels[4:14, 5:15] = 4  # upper clothes
    original = _image()

    result = isolate_garment_with_result(
        original,
        runner=FakeSegmenter(labels),
    )

    assert result.applied is True
    assert result.person_detected is True
    assert result.fallback_used is False
    assert result.garment_fraction == 100 / 320
    assert result.image != original
    crop = Image.open(BytesIO(result.image))
    assert crop.format == "PNG"
    assert crop.width < 20


def test_flat_lay_without_person_is_left_byte_for_byte_unchanged() -> None:
    labels = np.zeros((16, 20), dtype=np.int16)
    labels[2:14, 4:16] = 7
    original = _image()

    result = isolate_garment_with_result(
        original,
        runner=FakeSegmenter(labels),
    )

    assert result.image is original
    assert result.applied is False
    assert result.person_detected is False


def test_person_without_clothing_mask_uses_original_fallback() -> None:
    labels = np.zeros((16, 20), dtype=np.int16)
    labels[2:8, 5:15] = 11
    original = _image()

    result = isolate_garment_with_result(
        original,
        runner=FakeSegmenter(labels),
    )

    assert result.image is original
    assert result.fallback_used is True
    assert result.person_detected is True
    assert result.fallback_reason == "person detected but no garment mask found"


def test_model_failure_uses_exact_original_image() -> None:
    original = _image()

    isolated = isolate_garment(
        original,
        runner=FakeSegmenter(RuntimeError("model offline")),
    )

    assert isolated is original


def test_invalid_segmentation_shape_uses_original_fallback() -> None:
    original = _image()

    result = isolate_garment_with_result(
        original,
        runner=FakeSegmenter(np.zeros((2, 2), dtype=np.int16)),
    )

    assert result.image is original
    assert result.fallback_used is True
    assert result.fallback_reason is not None
    assert "expected segmentation shape" in result.fallback_reason


def test_activation_gate_requires_strictly_positive_recall_gain(tmp_path) -> None:
    report_path = tmp_path / "report.json"
    report_path.write_text(
        json.dumps(
            {
                "activated": True,
                "recall_at_10": {"gain": 0.01},
            }
        ),
        encoding="utf-8",
    )

    assert get_active_image_transform(report_path) is isolate_garment

    report_path.write_text(
        json.dumps(
            {
                "activated": False,
                "recall_at_10": {"gain": 0.0},
            }
        ),
        encoding="utf-8",
    )
    assert get_active_image_transform(report_path) is None


def test_missing_or_invalid_report_keeps_segmentation_disabled(tmp_path) -> None:
    report_path = tmp_path / "missing.json"
    assert get_active_image_transform(report_path) is None

    report_path.write_text("not-json", encoding="utf-8")
    assert get_active_image_transform(report_path) is None
