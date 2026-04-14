#!/usr/bin/env python3
"""Download and validate the three open-source AI models used by SwipeWear.

Models (all CPU-compatible, no GPU required — blueprint §13):
  1. FashionSigLIP  Marqo/marqo-fashionSigLIP  (via open_clip)  768-dim
  2. Qwen3-VL-2B    Qwen/Qwen3-VL-2B-Instruct  (via transformers, int8)
  3. GLiNER         urchade/gliner_multi-v2.1   (via gliner)

Usage:
    cd backend
    python scripts/setup_models.py              # all three models
    python scripts/setup_models.py --skip-qwen  # skip Qwen (slow, 2-4 GB)
    python scripts/setup_models.py --model fashionsiglip

Exit code: 0 = all requested models OK, 1 = any failure.
"""
from __future__ import annotations

import argparse
import io
import logging
import os
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
_LOG = logging.getLogger("setup_models")

# Allow running from either backend/ or repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

_FASHIONSIGLIP_REPO = os.getenv("FASHIONSIGLIP_MODEL", "hf-hub:Marqo/marqo-fashionSigLIP")
_QWEN_REPO = os.getenv("QWEN_MODEL", "Qwen/Qwen3-VL-2B-Instruct")
_GLINER_REPO = os.getenv("GLINER_MODEL", "urchade/gliner_multi-v2.1")

_VECTOR_DIM = 768


# ─── helpers ────────────────────────────────────────────────────────────────

def _ok(name: str, elapsed: float) -> bool:
    _LOG.info("✅  %-20s PASS  (%.1f s)", name, elapsed)
    return True


def _fail(name: str, exc: Exception) -> bool:
    _LOG.error("❌  %-20s FAIL  %s: %s", name, type(exc).__name__, exc)
    return False


# ─── model validators ───────────────────────────────────────────────────────

def check_fashionsiglip() -> bool:
    name = "FashionSigLIP"
    _LOG.info("→ Loading %s from %s …", name, _FASHIONSIGLIP_REPO)
    t0 = time.monotonic()
    try:
        import numpy as np
        import open_clip  # type: ignore[import]
        import torch  # type: ignore[import]
        from PIL import Image  # type: ignore[import]

        model, _, preprocess = open_clip.create_model_and_transforms(_FASHIONSIGLIP_REPO)
        model.eval()

        # Smoke test: encode a 224×224 white image
        img = Image.new("RGB", (224, 224), color=(255, 255, 255))
        tensor = preprocess(img).unsqueeze(0)
        with torch.no_grad():
            feats = model.encode_image(tensor)
        vec = feats.squeeze(0).cpu().numpy().astype(np.float32)

        assert vec.shape == (_VECTOR_DIM,), f"expected ({_VECTOR_DIM},), got {vec.shape}"
        norm = float(np.linalg.norm(vec))
        assert 0.99 < norm < 1.01 or norm > 0, f"norm={norm:.4f} (vector is all-zeros?)"
        _LOG.info("   dim=%d  norm=%.4f", vec.shape[0], norm)
        return _ok(name, time.monotonic() - t0)
    except Exception as exc:
        return _fail(name, exc)


def check_qwen() -> bool:
    name = "Qwen3-VL-2B"
    _LOG.info("→ Loading %s from %s (may take several minutes) …", name, _QWEN_REPO)
    t0 = time.monotonic()
    try:
        from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration  # type: ignore[import]
        import torch  # type: ignore[import]

        processor = AutoProcessor.from_pretrained(_QWEN_REPO, trust_remote_code=True)
        model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            _QWEN_REPO,
            torch_dtype="auto",
            device_map="cpu",
            trust_remote_code=True,
        )
        model.eval()

        # Smoke test: minimal text-only generation
        messages = [{"role": "user", "content": [{"type": "text", "text": "Say OK"}]}]
        text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = processor(text=[text], return_tensors="pt")
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=4)
        decoded = processor.decode(out[0], skip_special_tokens=True)
        assert decoded.strip(), "Model generated empty output"
        _LOG.info("   sample output: %r", decoded.strip()[:80])
        return _ok(name, time.monotonic() - t0)
    except Exception as exc:
        return _fail(name, exc)


def check_gliner() -> bool:
    name = "GLiNER"
    _LOG.info("→ Loading %s from %s …", name, _GLINER_REPO)
    t0 = time.monotonic()
    try:
        from gliner import GLiNER  # type: ignore[import]

        model = GLiNER.from_pretrained(_GLINER_REPO)

        # Smoke test: parse a real eBay-style fashion title
        title = "Nike Air Max 90 Baskets Homme Taille 42 Blanc Excellent état"
        labels = ["marque", "modèle", "taille", "couleur", "état"]
        entities = model.predict_entities(title, labels, threshold=0.3)

        assert isinstance(entities, list), "Expected list output"
        found = {e["label"] for e in entities}
        _LOG.info("   entities found: %s", {e["label"]: e["text"] for e in entities})
        assert found, "No entities detected — model may not have loaded properly"
        return _ok(name, time.monotonic() - t0)
    except Exception as exc:
        return _fail(name, exc)


# ─── main ───────────────────────────────────────────────────────────────────

_CHECKS = {
    "fashionsiglip": check_fashionsiglip,
    "qwen": check_qwen,
    "gliner": check_gliner,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Download and validate SwipeWear AI models")
    parser.add_argument(
        "--model",
        choices=list(_CHECKS),
        help="Run only one specific model check",
    )
    parser.add_argument(
        "--skip-qwen",
        action="store_true",
        help="Skip Qwen3-VL-2B (2-4 GB download, slow on CPU)",
    )
    args = parser.parse_args()

    if args.model:
        selected = {args.model: _CHECKS[args.model]}
    elif args.skip_qwen:
        selected = {k: v for k, v in _CHECKS.items() if k != "qwen"}
    else:
        selected = _CHECKS

    _LOG.info("SwipeWear model setup — checking %d model(s)", len(selected))
    _LOG.info("HuggingFace cache: %s", os.getenv("HF_HOME", "~/.cache/huggingface"))
    _LOG.info("")

    results: dict[str, bool] = {}
    for key, check_fn in selected.items():
        results[key] = check_fn()
        _LOG.info("")

    passed = sum(results.values())
    total = len(results)
    _LOG.info("─" * 50)
    _LOG.info("Result: %d/%d models OK", passed, total)

    if passed < total:
        failed = [k for k, ok in results.items() if not ok]
        _LOG.error("Failed: %s", ", ".join(failed))
        _LOG.error("")
        _LOG.error("Troubleshooting:")
        _LOG.error("  pip install open_clip_torch transformers gliner torch Pillow")
        _LOG.error("  export HF_HOME=/path/to/large/disk  # if disk space is limited")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
