"""Official q4f16 ONNX export adapter for Marqo FashionSigLIP."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

MODEL_ID = "Marqo/marqo-fashionSigLIP"
EMBEDDING_VERSION = "fashionsiglip-q4f16-onnx-v1"
VECTOR_DIM = 768
IMAGE_SIZE = 224
CONTEXT_LENGTH = 64


class OnnxFashionSigLIPService:
    """FashionSigLIP image/text embeddings via its official q4f16 ONNX files."""

    embedding_version = EMBEDDING_VERSION
    vector_dim = VECTOR_DIM

    def __init__(
        self,
        model_dir: Path,
        tokenizer_dir: Path,
        *,
        vision_only: bool = False,
        vision_model_path: Path | None = None,
        text_model_path: Path | None = None,
        vision_session: Any | None = None,
        text_session: Any | None = None,
        tokenizer: Any | None = None,
    ) -> None:
        if vision_session is None or (text_session is None and not vision_only):
            import onnxruntime as ort  # type: ignore[import-untyped]

            options = ort.SessionOptions()
            # q4f16 exports currently trip ORT's SimplifiedLayerNormFusion.
            options.graph_optimization_level = (
                ort.GraphOptimizationLevel.ORT_DISABLE_ALL
            )
            vision_session = vision_session or ort.InferenceSession(
                str(
                    vision_model_path
                    or model_dir / "vision_model_q4f16.onnx"
                ),
                sess_options=options,
                providers=["CPUExecutionProvider"],
            )
            if not vision_only:
                text_session = text_session or ort.InferenceSession(
                    str(text_model_path or model_dir / "text_model_q4f16.onnx"),
                    sess_options=options,
                    providers=["CPUExecutionProvider"],
                )
        if tokenizer is None and not vision_only:
            from transformers import AutoTokenizer

            tokenizer = AutoTokenizer.from_pretrained(
                tokenizer_dir,
                local_files_only=True,
            )
        self._vision_session = vision_session
        self._text_session = text_session
        self._tokenizer = tokenizer
        self.supports_text = not vision_only

    def encode_image(self, image: bytes) -> np.ndarray:
        pixels = _preprocess_image(image)
        input_name = self._vision_session.get_inputs()[0].name
        outputs = self._vision_session.run(None, {input_name: pixels})
        return _normalized_embedding(outputs)

    def encode_text(self, text: str) -> np.ndarray:
        if self._text_session is None or self._tokenizer is None:
            raise RuntimeError("text encoding is unavailable in vision-only mode")
        tokens = self._tokenizer(
            [text],
            padding="max_length",
            truncation=True,
            max_length=CONTEXT_LENGTH,
            return_tensors="np",
        )
        available = {item.name for item in self._text_session.get_inputs()}
        inputs = {
            name: np.asarray(value, dtype=np.int64)
            for name, value in tokens.items()
            if name in available
        }
        if not inputs:
            raise ValueError("tokenizer produced no inputs accepted by text model")
        outputs = self._text_session.run(None, inputs)
        return _normalized_embedding(outputs)


def _preprocess_image(image: bytes) -> np.ndarray:
    source = Image.open(BytesIO(image)).convert("RGB")
    resized = source.resize(
        (IMAGE_SIZE, IMAGE_SIZE),
        resample=Image.Resampling.BICUBIC,
    )
    pixels = np.asarray(resized, dtype=np.float32) / 255.0
    pixels = (pixels - 0.5) / 0.5
    return np.transpose(pixels, (2, 0, 1))[None, ...].astype(np.float32)


def _normalized_embedding(outputs: list[np.ndarray]) -> np.ndarray:
    candidates = [
        np.asarray(output, dtype=np.float32)
        for output in outputs
        if np.asarray(output).shape == (1, VECTOR_DIM)
    ]
    if not candidates:
        shapes = [np.asarray(output).shape for output in outputs]
        raise ValueError(
            f"ONNX model did not return a (1, {VECTOR_DIM}) embedding: {shapes}"
        )
    vector = candidates[-1][0]
    if not np.isfinite(vector).all():
        raise ValueError("embedding contains non-finite values")
    norm = float(np.linalg.norm(vector))
    if norm == 0.0:
        raise ValueError("embedding has zero norm")
    return (vector / norm).astype(np.float32)
