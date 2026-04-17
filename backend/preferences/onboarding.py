"""Onboarding route A -- style grid cold start (KAN-33, blueprint SS6).

A brand-new user has no swipe history. Route A shows a grid of visual style
archetypes; picking a few builds an immediately usable UserPreferenceProfile
for the very first feed, before any real InteractionEvent exists.

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
"""
from __future__ import annotations

import json
import logging
import random
from math import sqrt
from pathlib import Path

from contracts.profile import StyleVectors, UserPreferenceProfile

_LOG = logging.getLogger("swipewear.preferences.onboarding")

VECTOR_DIM = 768

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
