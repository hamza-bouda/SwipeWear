from __future__ import annotations

import json
from io import BytesIO

import numpy as np
import pytest
from PIL import Image
from pydantic import ValidationError

from vision.interfaces import GarmentBox, SceneAnalysis
from vision.qwen import QwenSceneAnalyzer, encode_scene_for_profile


def _image(color: str = "white") -> bytes:
    output = BytesIO()
    Image.new("RGB", (100, 80), color=color).save(output, format="JPEG")
    return output.getvalue()


def _response(*, garment_count: int = 2) -> str:
    categories = ("shirt", "pants")
    garments = [
        [
            categories[index],
            "blue" if index == 0 else "black",
            "casual",
            0.05 + index * 0.45,
            0.1,
            0.45 + index * 0.45,
            0.9,
        ]
        for index in range(garment_count)
    ]
    return json.dumps(
        {
            "g": garments,
            "t": ["streetwear", "layered"],
            "c": 0.88,
        }
    )


class FakeRunner:
    model_id = "fake-qwen"

    def __init__(self, responses: list[str | Exception]) -> None:
        self.responses = iter(responses)
        self.prompts: list[str] = []

    def generate(self, image: bytes, prompt: str) -> str:
        self.prompts.append(prompt)
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return response


class FakeEmbeddingService:
    embedding_version = "fake-v1"
    vector_dim = 4

    def __init__(self, vectors: list[np.ndarray]) -> None:
        self.vectors = iter(vectors)
        self.images: list[bytes] = []

    def encode_image(self, image: bytes) -> np.ndarray:
        self.images.append(image)
        return next(self.vectors)

    def encode_text(self, text: str) -> np.ndarray:
        raise NotImplementedError


def test_valid_scene_json_produces_structured_garments_and_crops() -> None:
    result = QwenSceneAnalyzer(FakeRunner([_response()])).analyze(_image())

    assert len(result.garments) == 2
    assert result.garments[0].category == "shirt"
    assert result.global_tags == ["streetwear", "layered"]
    assert result.confidence == 0.88
    assert len(result.garment_crops) == 2
    assert result.model == "fake-qwen"
    assert result.fallback_used is False
    assert result.requires_tag_confirmation is False

    crop_sizes = [Image.open(BytesIO(crop)).size for crop in result.garment_crops]
    assert crop_sizes == [(40, 64), (40, 64)]


def test_invalid_json_gets_exactly_one_successful_repair() -> None:
    runner = FakeRunner(["not json", _response()])

    result = QwenSceneAnalyzer(runner).analyze(_image())

    assert len(runner.prompts) == 2
    assert "Invalid response" in runner.prompts[1]
    assert result.fallback_used is False
    assert len(result.garments) == 2


def test_invalid_json_after_repair_uses_required_fallback() -> None:
    image = _image()
    runner = FakeRunner(["not json", "still not json"])

    result = QwenSceneAnalyzer(runner).analyze(image)

    assert len(runner.prompts) == 2
    assert result.garments == []
    assert result.global_tags == []
    assert result.confidence == 0.0
    assert result.garment_crops == [image]
    assert result.model == "fake-qwen"
    assert result.fallback_used is True
    assert result.requires_tag_confirmation is True
    assert result.fallback_reason is not None
    assert result.fallback_reason.startswith("ValueError:")


def test_model_failure_uses_fallback_without_repair() -> None:
    image = _image()
    runner = FakeRunner([RuntimeError("model unavailable")])

    result = QwenSceneAnalyzer(runner).analyze(image)

    assert len(runner.prompts) == 1
    assert result.fallback_used is True
    assert result.garment_crops == [image]


def test_crop_embeddings_are_averaged_and_normalized_for_profile() -> None:
    analysis = QwenSceneAnalyzer(FakeRunner([_response()])).analyze(_image())
    service = FakeEmbeddingService(
        [
            np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32),
            np.array([0.0, 1.0, 0.0, 0.0], dtype=np.float32),
        ]
    )

    vector = encode_scene_for_profile(_image(), analysis, service)

    expected = np.array([1.0, 1.0, 0.0, 0.0], dtype=np.float32)
    expected /= np.linalg.norm(expected)
    np.testing.assert_allclose(vector, expected)
    assert service.images == analysis.garment_crops


def test_fallback_encodes_whole_image_and_requests_tag_confirmation() -> None:
    image = _image()
    analysis = QwenSceneAnalyzer(FakeRunner([RuntimeError("offline")])).analyze(
        image
    )
    service = FakeEmbeddingService(
        [np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)]
    )

    vector = encode_scene_for_profile(image, analysis, service)

    np.testing.assert_array_equal(
        vector,
        np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32),
    )
    assert service.images == [image]
    assert analysis.requires_tag_confirmation is True


@pytest.mark.parametrize("color", ["white", "gray", "navy"])
def test_three_outfit_photos_each_detect_at_least_two_garments(color: str) -> None:
    result = QwenSceneAnalyzer(FakeRunner([_response()])).analyze(_image(color))

    assert len(result.garments) >= 2


def test_garment_box_rejects_non_positive_area() -> None:
    with pytest.raises(ValidationError, match="positive area"):
        GarmentBox(x_min=0.5, y_min=0.1, x_max=0.5, y_max=0.9)


def test_compact_protocol_requires_exactly_two_garments() -> None:
    result = QwenSceneAnalyzer(
        FakeRunner([_response(garment_count=1), _response(garment_count=1)])
    ).analyze(_image())

    assert result.fallback_used is True
    assert result.requires_tag_confirmation is True


def test_qwen_native_coordinates_are_normalized_before_validation() -> None:
    response = json.dumps(
        {
            "g": [
                ["coat", "blue", "formal", 100, 50, 600, 950],
                ["skirt", "black", "pleated", 250, 550, 750, 999],
            ],
            "t": ["formal"],
            "c": 0.9,
        }
    )

    result = QwenSceneAnalyzer(FakeRunner([response])).analyze(_image())

    assert result.fallback_used is False
    assert result.garments[0].box.x_min == 0.1
    assert result.garments[1].box.y_max == 0.999


def test_reversed_qwen_box_corners_are_canonicalized() -> None:
    response = json.dumps(
        {
            "g": [
                ["shirt", "white", "casual", 800, 900, 200, 100],
                ["pants", "blue", "denim", 700, 950, 300, 500],
            ],
            "t": ["casual"],
            "c": 0.8,
        }
    )

    result = QwenSceneAnalyzer(FakeRunner([response])).analyze(_image())

    assert result.fallback_used is False
    assert result.garments[0].box.model_dump() == {
        "x_min": 0.2,
        "y_min": 0.1,
        "x_max": 0.8,
        "y_max": 0.9,
    }


def test_degenerate_approximate_box_is_expanded_to_a_usable_crop() -> None:
    response = json.dumps(
        {
            "g": [
                ["shirt", "white", "casual", 150, 750, 200, 750],
                ["pants", "blue", "denim", 400, 500, 400, 900],
            ],
            "t": ["casual"],
            "c": 0.8,
        }
    )

    result = QwenSceneAnalyzer(FakeRunner([response])).analyze(_image())

    assert result.fallback_used is False
    assert result.garments[0].box.y_min == 0.725
    assert result.garments[0].box.y_max == 0.775
    assert result.garments[1].box.x_min == 0.375
    assert result.garments[1].box.x_max == pytest.approx(0.425)
    assert all(Image.open(BytesIO(crop)).size[0] > 0 for crop in result.garment_crops)


def test_generic_garment_category_triggers_single_repair() -> None:
    generic = _response().replace('"shirt"', '"garment"', 1)
    runner = FakeRunner([generic, _response()])

    result = QwenSceneAnalyzer(runner).analyze(_image())

    assert result.fallback_used is False
    assert len(runner.prompts) == 2
    assert result.garments[0].category == "shirt"


def test_out_of_range_qwen_coordinates_are_clamped_to_image_bounds() -> None:
    response = json.dumps(
        {
            "g": [
                ["dress", "cream", "formal", -50, 100, 1200, 1100],
                ["coat", "brown", "winter", 100, 50, 1500, 999],
            ],
            "t": ["store"],
            "c": 0.75,
        }
    )

    result = QwenSceneAnalyzer(FakeRunner([response])).analyze(_image())

    assert result.fallback_used is False
    assert result.garments[0].box.x_min == 0.0
    assert result.garments[0].box.x_max == 1.0
    assert result.garments[0].box.y_max == 1.0
