"""Onboarding routes A & B -- cold start (KAN-33/KAN-34, blueprint SS6).

A brand-new user has no swipe history. Route A (build_profile_from_styles)
shows a grid of visual style archetypes. Route B (build_profile_from_images)
lets the user import their own inspiration photos instead -- both build the
same UserPreferenceProfile shape for the very first feed, before any real
InteractionEvent exists.

Archetype embeddings (data/style_archetype_embeddings.json) are REAL
FashionSigLIP output (KAN-77 confirmed the model's true output is 768-dim,
not 512), computed from real reference photos -- 3 men's + 3 women's outfits
per style, averaged and L2-normalised per archetype. If that data file is
ever missing (e.g. a stripped-down checkout), this falls back to
deterministic placeholder vectors with a warning rather than crashing
onboarding -- a real style-vector mismatch is better caught by product
review than by a hard failure at import time.

Ids are kept in sync with mobile/src/data/styleArchetypes.ts so a style
selected in the app resolves to the right entry here.

build_profile_from_images takes an injected EmbeddingService rather than
importing embeddings.fashionsiglip directly -- preferences/ may only import
another module's interfaces.py (blueprint SS11 / lint_imports.py), the same
pattern vision/qwen.py uses for encode_scene_for_profile. It is also
FashionSigLIP-only for now: KAN-34's ticket describes an optional Qwen
scene-analysis branch (tags feeding editable_preferences), but KAN-30's
bench came back DEFER (270s/image on CPU vs a 3s target), so that branch
is not wired -- this always takes the ticket's own documented fallback path.
"""
from __future__ import annotations

import json
import logging
import random
from math import sqrt
from pathlib import Path

import numpy as np

from contracts.profile import StyleVectors, UserPreferenceProfile
from embeddings.interfaces import EmbeddingService

_LOG = logging.getLogger("swipewear.preferences.onboarding")

VECTOR_DIM = 768
MAX_ONBOARDING_IMAGES = 10
MAX_ONBOARDING_IMAGE_BYTES = 5 * 1024 * 1024

STYLE_ARCHETYPE_IDS = [
    "streetwear",
    "minimalist",
    "vintage",
    "sport",
    "workwear",
    "preppy",
    "grunge",
    "bohemian",
    "techwear",
    "casual",
]

_DATA_FILE = Path(__file__).parent / "data" / "style_archetype_embeddings.json"


def _l2_normalize(vector: list[float]) -> list[float]:
    norm = sqrt(sum(v * v for v in vector))
    if norm == 0.0:
        return vector
    return [v / norm for v in vector]


def _placeholder_embedding(style_id: str) -> list[float]:
    rng = random.Random(f"style-archetype:{style_id}")
    raw = [rng.uniform(-1.0, 1.0) for _ in range(VECTOR_DIM)]
    return _l2_normalize(raw)


def _load_archetype_embeddings() -> dict[str, list[float]]:
    try:
        with open(_DATA_FILE, encoding="utf-8") as f:
            data = json.load(f)
        missing = [s for s in STYLE_ARCHETYPE_IDS if s not in data]
        if missing:
            raise ValueError(f"missing styles in data file: {missing}")
        return {style_id: data[style_id] for style_id in STYLE_ARCHETYPE_IDS}
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        _LOG.warning(
            "Falling back to placeholder archetype embeddings: %s", exc,
        )
        return {
            style_id: _placeholder_embedding(style_id)
            for style_id in STYLE_ARCHETYPE_IDS
        }


ARCHETYPE_EMBEDDINGS: dict[str, list[float]] = _load_archetype_embeddings()


def build_profile_from_styles(selected_style_ids: list[str]) -> UserPreferenceProfile:
    """Build a v1 profile from onboarding style-grid picks.

    Unknown ids are ignored rather than raising -- this is a user-input
    boundary (the onboarding screen), not an internal invariant. An empty
    or all-unknown selection returns a valid, cold-start profile (null
    vector, caller falls back to a popularity-based feed).
    """
    embeddings = [
        ARCHETYPE_EMBEDDINGS[style_id]
        for style_id in selected_style_ids
        if style_id in ARCHETYPE_EMBEDDINGS
    ]

    if not embeddings:
        return UserPreferenceProfile()

    dim = len(embeddings[0])
    averaged = [
        sum(vec[i] for vec in embeddings) / len(embeddings)
        for i in range(dim)
    ]
    style_vector = _l2_normalize(averaged)

    return UserPreferenceProfile(
        vectors=StyleVectors(positive=style_vector),
    )


def build_profile_from_images(
    image_paths: list[str],
    embedding_service: EmbeddingService,
) -> UserPreferenceProfile:
    """Build a v1 profile from onboarding inspiration-image imports (route B).

    More than MAX_ONBOARDING_IMAGES raises -- that's a request-shape limit
    the caller (API layer) is expected to enforce up front. A single image
    that is oversized, unreadable, or fails to encode is skipped instead of
    failing the whole import, same philosophy as Qwen's mandatory fallback:
    one bad photo must not crash onboarding. An empty or all-skipped
    selection returns a valid cold-start profile, same as
    build_profile_from_styles.
    """
    if len(image_paths) > MAX_ONBOARDING_IMAGES:
        raise ValueError(
            f"at most {MAX_ONBOARDING_IMAGES} images allowed, "
            f"got {len(image_paths)}",
        )

    vectors: list[np.ndarray] = []
    for path in image_paths:
        try:
            data = Path(path).read_bytes()
        except OSError as exc:
            _LOG.warning("Skipping unreadable onboarding image %s: %s", path, exc)
            continue
        if len(data) > MAX_ONBOARDING_IMAGE_BYTES:
            _LOG.warning(
                "Skipping oversized onboarding image %s (%d bytes)",
                path,
                len(data),
            )
            continue
        try:
            vectors.append(np.asarray(embedding_service.encode_image(data), dtype=np.float32))
        except Exception as exc:  # noqa: BLE001 - one bad image must not fail onboarding
            _LOG.warning("Skipping onboarding image %s that failed to encode: %s", path, exc)
            continue

    if not vectors:
        return UserPreferenceProfile()

    mean_vector = np.mean(np.stack(vectors), axis=0).tolist()
    style_vector = _l2_normalize(mean_vector)

    return UserPreferenceProfile(
        vectors=StyleVectors(positive=style_vector),
    )
