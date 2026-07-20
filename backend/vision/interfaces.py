from __future__ import annotations
from dataclasses import dataclass

@dataclass
class SceneAnalysisResult:
    tags: list[str]
    garment_crops: list[bytes]
    model: str = "qwen3-vl-2b-instruct"
    fallback_used: bool = False

async def analyze_scene(image_bytes: bytes) -> SceneAnalysisResult:
    # Qwen3-VL-2B-Instruct on CPU. Fallback: empty tags, embeddings module handles image alone.
    raise NotImplementedError
