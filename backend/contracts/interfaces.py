"""
Shared contracts — Pydantic schemas used by every module.

CHANGELOG_contracts.md must be updated for any breaking change.
Every schema carries a schema_version field.
"""
from __future__ import annotations


# ---------------------------------------------------------------------------
# Interaction events — canonical schema lives in contracts/events.py (KAN-18)
# ---------------------------------------------------------------------------

from contracts.events import EventType, InteractionEvent  # noqa: E402, F401


# ---------------------------------------------------------------------------
# User preference profile — canonical schema lives in contracts/profile.py (KAN-17)
# ---------------------------------------------------------------------------

from contracts.profile import (  # noqa: E402, F401
    EditablePreferences,
    HardConstraints,
    LockedAttribute,
    StyleVectors,
    UserPreferenceProfile,
)


# ---------------------------------------------------------------------------
# Product catalogue — canonical schema lives in contracts/product.py (KAN-16)
# ---------------------------------------------------------------------------

from contracts.product import ProductCondition, ProductRecord, ProductSource  # noqa: E402, F401


# ---------------------------------------------------------------------------
# Pipeline contracts — canonical schema lives in contracts/pipeline.py (KAN-19)
# ---------------------------------------------------------------------------

from contracts.pipeline import (  # noqa: E402, F401
    CandidateItem,
    CandidateSet,
    Explanation,
    ModuleTrace,
    PriceLadderEntry,
    RankedFeed,
    RankedItem,
    RecoRequest,
)
