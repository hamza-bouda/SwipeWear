from __future__ import annotations

from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image

from embeddings.fashionsiglip_onnx import (
    VECTOR_DIM,
    OnnxFashionSigLIPService,
)


def _image() -> bytes:
    output = BytesIO()
    Image.new("RGB", (40, 20), color=(255, 128, 0)).save(output, format="PNG")
    return output.getvalue()


class FakeSession:
    def __init__(self, input_names: list[str], output: np.ndarray) -> None:
        self.input_names = input_names
        self.output = output
        self.calls: list[dict[str, np.ndarray]] = []

    def get_inputs(self):
        return [SimpleNamespace(name=name) for name in self.input_names]

    def run(self, output_names, inputs):
        self.calls.append(inputs)
        return [self.output]


class FakeTokenizer:
    def __call__(self, texts, **kwargs):
        return {
            "input_ids": np.ones((1, 64), dtype=np.int64),
            "attention_mask": np.ones((1, 64), dtype=np.int64),
            "ignored": np.zeros((1, 64), dtype=np.int64),
        }


def _service(output: np.ndarray) -> tuple[OnnxFashionSigLIPService, FakeSession, FakeSession]:
    vision = FakeSession(["pixel_values"], output)
    text = FakeSession(["input_ids", "attention_mask"], output)
    service = OnnxFashionSigLIPService(
        Path("unused"),
        Path("unused"),
        vision_session=vision,
        text_session=text,
        tokenizer=FakeTokenizer(),
    )
    return service, vision, text


def test_official_onnx_adapter_encodes_and_normalizes_image() -> None:
    output = np.arange(1, VECTOR_DIM + 1, dtype=np.float32)[None, :]
    service, vision, _ = _service(output)

    vector = service.encode_image(_image())

    assert vector.shape == (VECTOR_DIM,)
    assert np.linalg.norm(vector) == pytest.approx(1.0)
    pixels = vision.calls[0]["pixel_values"]
    assert pixels.shape == (1, 3, 224, 224)
    assert pixels.dtype == np.float32


def test_official_onnx_adapter_filters_tokenizer_inputs() -> None:
    output = np.ones((1, VECTOR_DIM), dtype=np.float32)
    service, _, text = _service(output)

    vector = service.encode_text("a jacket")

    assert vector.shape == (VECTOR_DIM,)
    assert set(text.calls[0]) == {"input_ids", "attention_mask"}


def test_vision_only_adapter_does_not_require_text_model() -> None:
    output = np.ones((1, VECTOR_DIM), dtype=np.float32)
    vision = FakeSession(["pixel_values"], output)
    service = OnnxFashionSigLIPService(
        Path("unused"),
        Path("unused"),
        vision_only=True,
        vision_session=vision,
    )

    assert service.encode_image(_image()).shape == (VECTOR_DIM,)
    assert service.supports_text is False
    with pytest.raises(RuntimeError, match="vision-only"):
        service.encode_text("a jacket")


@pytest.mark.parametrize(
    "output",
    [
        np.zeros((1, VECTOR_DIM), dtype=np.float32),
        np.full((1, VECTOR_DIM), np.nan, dtype=np.float32),
        np.ones((1, 512), dtype=np.float32),
    ],
)
def test_invalid_onnx_output_is_rejected(output: np.ndarray) -> None:
    service, _, _ = _service(output)

    with pytest.raises(ValueError):
        service.encode_image(_image())
