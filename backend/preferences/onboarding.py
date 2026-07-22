"""Onboarding route A -- style grid cold start (KAN-33, blueprint SS6).

A brand-new user has no swipe history. Route A shows a grid of visual style
archetypes; picking a few builds an immediately usable UserPreferenceProfile
for the very first feed, before any real InteractionEvent exists.

Archetype embeddings below are DETERMINISTIC PLACEHOLDERS (seeded random unit
vectors), not real FashionSigLIP output -- there are no reference photos for
these archetypes in the repo yet to run the actual embedding pipeline against
(see embeddings/indexer.py for how real product embeddings are computed).
Swap ARCHETYPE_EMBEDDINGS for real precomputed vectors once reference images
exist; the ids here are kept in sync with mobile/src/data/styleArchetypes.ts
so a style selected in the app resolves to the right entry here.
"""
from __future__ import annotations

import random
from math import sqrt

from contracts.profile import StyleVectors, UserPreferenceProfile

VECTOR_DIM = 512

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


def _l2_normalize(vector: list[float]) -> list[float]:
    norm = sqrt(sum(v * v for v in vector))
    if norm == 0.0:
        return vector
    return [v / norm for v in vector]


def _placeholder_embedding(style_id: str) -> list[float]:
    rng = random.Random(f"style-archetype:{style_id}")
    raw = [rng.uniform(-1.0, 1.0) for _ in range(VECTOR_DIM)]
    return _l2_normalize(raw)


ARCHETYPE_EMBEDDINGS: dict[str, list[float]] = {
    style_id: _placeholder_embedding(style_id) for style_id in STYLE_ARCHETYPE_IDS
}


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
