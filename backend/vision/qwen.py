"""Qwen3-VL scene analyzer with validated JSON, repair, and safe fallback."""
from __future__ import annotations

import json
import logging
from io import BytesIO
from typing import Any, Literal, Protocol

import numpy as np
from PIL import Image
from pydantic import BaseModel, Field, ValidationError

from embeddings.interfaces import EmbeddingService
from vision.interfaces import DetectedGarment, GarmentBox, SceneAnalysis

MODEL_ID = "Qwen/Qwen3-VL-2B-Instruct"
_LOG = logging.getLogger("swipewear.vision.qwen")
GARMENT_CATEGORIES = frozenset(
    {
        "blouse",
        "coat",
        "dress",
        "hoodie",
        "jacket",
        "pants",
        "shirt",
        "shorts",
        "skirt",
        "sweater",
        "t-shirt",
        "vest",
    }
)

_SCENE_PROMPT = (
    "Identify exactly the 2 most prominent garments in this fashion image. "
    "Return ONLY compact one-line JSON with this exact shape:\n"
    '{"g":[["category","color","style",x1,y1,x2,y2],'
    '["category","color","style",x1,y1,x2,y2]],'
    '"t":["outfit tag"],"c":0.0}\n'
    "Category must be exactly one of: blouse, coat, dress, hoodie, jacket, "
    "pants, shirt, shorts, skirt, sweater, t-shirt, vest. Never use 'garment'. "
    "The four coordinates use Qwen's 0..1000 bounding-box scale. Exclude "
    "people, bags, jewelry, furniture, and background. No markdown or commentary."
)

_REPAIR_PROMPT = (
    "Correct the response into ONLY compact one-line JSON:\n"
    '{{"g":[["category","color","style",x1,y1,x2,y2],'
    '["category","color","style",x1,y1,x2,y2]],'
    '"t":["outfit tag"],"c":0.0}}\n'
    "Use exactly 2 items. Category must be one of blouse, coat, dress, hoodie, "
    "jacket, pants, shirt, shorts, skirt, sweater, t-shirt, vest; never garment. "
    "Use coordinates on a 0..1000 scale and no commentary.\n\n"
    "Invalid response:\n{response}\n"
)


class VisionLanguageRunner(Protocol):
    """Minimal Qwen generation boundary used by production and tests."""

    model_id: str

    def generate(self, image: bytes, prompt: str) -> str:
        """Generate text for one image and prompt."""
        ...


class _ScenePayload(BaseModel):
    garments: list[DetectedGarment] = Field(min_length=1)
    global_tags: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class _CompactScenePayload(BaseModel):
    g: list[tuple[str, str, str, float, float, float, float]] = Field(
        min_length=2,
        max_length=2,
    )
    t: list[str] = Field(default_factory=list)
    c: float = Field(ge=0.0, le=1.0)


class Qwen3VLRunner:
    """Lazy CPU-only Transformers + TorchAO Qwen runner."""

    def __init__(
        self,
        model_id: str = MODEL_ID,
        *,
        quantization: Literal["int8", "int4"] = "int8",
        max_new_tokens: int = 256,
    ) -> None:
        self.model_id = model_id
        self.quantization = quantization
        self.max_new_tokens = max_new_tokens
        self._model: Any | None = None
        self._processor: Any | None = None

    def _quantization_config(self) -> Any:
        from transformers import TorchAoConfig  # type: ignore[import-not-found]

        if self.quantization == "int8":
            from torchao.quantization import (  # type: ignore[import-untyped]
                Int8WeightOnlyConfig,
            )

            quant_type = Int8WeightOnlyConfig(group_size=128)
        else:
            from torchao.dtypes import Int4CPULayout  # type: ignore[import-untyped]
            from torchao.quantization import (  # type: ignore[import-untyped]
                Int4WeightOnlyConfig,
            )

            quant_type = Int4WeightOnlyConfig(
                group_size=128,
                layout=Int4CPULayout(),
            )
        return TorchAoConfig(quant_type=quant_type)

    def _load(self) -> tuple[Any, Any]:
        if self._model is None or self._processor is None:
            from transformers import AutoModelForMultimodalLM, AutoProcessor

            self._processor = AutoProcessor.from_pretrained(self.model_id)
            self._model = AutoModelForMultimodalLM.from_pretrained(
                self.model_id,
                device_map="cpu",
                dtype="auto",
                low_cpu_mem_usage=True,
                quantization_config=self._quantization_config(),
            )
            self._model.eval()
        return self._model, self._processor

    def generate(self, image: bytes, prompt: str) -> str:
        import torch

        model, processor = self._load()
        pil_image = Image.open(BytesIO(image)).convert("RGB")
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": pil_image},
                    {"type": "text", "text": prompt},
                ],
            }
        ]
        inputs = processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(model.device)
        input_length = inputs["input_ids"].shape[-1]
        with torch.inference_mode():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                disable_compile=True,
            )
        generated_ids = output_ids[0][input_length:]
        return processor.decode(
            generated_ids,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        ).strip()


class QwenSceneAnalyzer:
    """SceneAnalyzer implementation with one repair attempt then fallback."""

    def __init__(self, runner: VisionLanguageRunner | None = None) -> None:
        self._runner = runner or Qwen3VLRunner()

    def analyze(self, image: bytes) -> SceneAnalysis:
        raw_response: str | None = None
        try:
            raw_response = self._runner.generate(image, _SCENE_PROMPT)
            payload = _parse_payload(raw_response)
        except (json.JSONDecodeError, ValidationError, ValueError) as first_error:
            _LOG.warning(
                "Qwen scene JSON invalid; attempting one repair: %s",
                first_error,
                extra={"pipe_module": "vision.qwen", "repair_attempt": 1},
            )
            try:
                repaired = self._runner.generate(
                    image,
                    _REPAIR_PROMPT.format(response=raw_response or ""),
                )
                payload = _parse_payload(repaired)
            except Exception as repair_error:  # noqa: BLE001 - required safe fallback
                return _fallback(image, self._runner.model_id, repair_error)
        except Exception as model_error:  # noqa: BLE001 - model failure fallback
            return _fallback(image, self._runner.model_id, model_error)

        try:
            crops = _crop_garments(image, payload.garments)
        except Exception as crop_error:  # noqa: BLE001 - image fallback is mandatory
            return _fallback(image, self._runner.model_id, crop_error)
        if not crops:
            return _fallback(
                image,
                self._runner.model_id,
                ValueError("no usable garment crops"),
            )
        return SceneAnalysis(
            garments=payload.garments,
            global_tags=payload.global_tags,
            confidence=payload.confidence,
            garment_crops=crops,
            model=self._runner.model_id,
        )


def encode_scene_for_profile(
    image: bytes,
    analysis: SceneAnalysis,
    embedding_service: EmbeddingService,
) -> np.ndarray:
    """Encode garment crops and return their L2-normalized mean profile vector."""
    sources = analysis.garment_crops if not analysis.fallback_used else [image]
    if not sources:
        sources = [image]
    vectors = [
        _validate_vector(embedding_service.encode_image(source), embedding_service)
        for source in sources
    ]
    mean = np.mean(np.stack(vectors), axis=0).astype(np.float32)
    norm = float(np.linalg.norm(mean))
    return mean if norm == 0.0 else (mean / norm).astype(np.float32)


def _parse_payload(response: str) -> _ScenePayload:
    candidate = response.strip()
    if candidate.startswith("```"):
        lines = candidate.splitlines()
        candidate = "\n".join(lines[1:-1]).strip()
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start < 0 or end < start:
        raise ValueError("response does not contain a JSON object")
    decoded = json.loads(candidate[start : end + 1])
    if isinstance(decoded, dict) and "g" in decoded:
        compact = _CompactScenePayload.model_validate(decoded)
        for category, *_ in compact.g:
            if category.strip().lower() not in GARMENT_CATEGORIES:
                raise ValueError(f"unsupported garment category: {category}")
        garments = [
            DetectedGarment(
                category=category.strip().lower(),
                colors=[color],
                style=style,
                box=_normalized_box(x_min, y_min, x_max, y_max),
            )
            for category, color, style, x_min, y_min, x_max, y_max in compact.g
        ]
        return _ScenePayload(
            garments=garments,
            global_tags=compact.t,
            confidence=compact.c,
        )
    return _ScenePayload.model_validate(decoded)


def _normalized_box(
    x_min: float,
    y_min: float,
    x_max: float,
    y_max: float,
) -> GarmentBox:
    coordinates = (x_min, y_min, x_max, y_max)
    if any(coordinate > 1.0 for coordinate in coordinates):
        coordinates = (
            min(1.0, max(0.0, coordinates[0] / 1000.0)),
            min(1.0, max(0.0, coordinates[1] / 1000.0)),
            min(1.0, max(0.0, coordinates[2] / 1000.0)),
            min(1.0, max(0.0, coordinates[3] / 1000.0)),
        )
    x_min, x_max = _usable_interval(coordinates[0], coordinates[2])
    y_min, y_max = _usable_interval(coordinates[1], coordinates[3])
    return GarmentBox(
        x_min=x_min,
        y_min=y_min,
        x_max=x_max,
        y_max=y_max,
    )


def _usable_interval(first: float, second: float) -> tuple[float, float]:
    lower, upper = sorted((first, second))
    if upper > lower:
        return lower, upper
    half_minimum_span = 0.025
    return (
        max(0.0, lower - half_minimum_span),
        min(1.0, upper + half_minimum_span),
    )


def _crop_garments(
    image: bytes,
    garments: list[DetectedGarment],
) -> list[bytes]:
    source = Image.open(BytesIO(image)).convert("RGB")
    width, height = source.size
    crops: list[bytes] = []
    for garment in garments:
        box = garment.box
        pixel_box = (
            max(0, round(box.x_min * width)),
            max(0, round(box.y_min * height)),
            min(width, round(box.x_max * width)),
            min(height, round(box.y_max * height)),
        )
        crop = source.crop(pixel_box)
        output = BytesIO()
        crop.save(output, format="PNG")
        crops.append(output.getvalue())
    return crops


def _validate_vector(
    vector: np.ndarray,
    embedding_service: EmbeddingService,
) -> np.ndarray:
    result = np.asarray(vector, dtype=np.float32)
    if result.shape != (embedding_service.vector_dim,):
        raise ValueError(
            f"expected embedding shape ({embedding_service.vector_dim},), "
            f"got {result.shape}"
        )
    if not np.isfinite(result).all():
        raise ValueError("embedding contains non-finite values")
    return result


def _fallback(image: bytes, model_id: str, error: Exception) -> SceneAnalysis:
    _LOG.error(
        "Qwen scene analysis failed; using whole-image embedding fallback: %s",
        error,
        extra={"pipe_module": "vision.qwen", "fallback_used": True},
    )
    return SceneAnalysis(
        garments=[],
        global_tags=[],
        confidence=0.0,
        garment_crops=[image],
        model=model_id,
        fallback_used=True,
        fallback_reason=f"{type(error).__name__}: {error}",
        requires_tag_confirmation=True,
    )
