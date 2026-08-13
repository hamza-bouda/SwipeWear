"""
Shared contracts — Pydantic schemas used by every module.

CHANGELOG_contracts.md must be updated for any breaking change.
Every schema carries a schema_version field.
"""
from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SchemaVersion(str, Enum):
    v1 = "1.0"


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
# Retrieval / ranking
# ---------------------------------------------------------------------------

class CandidateItem(BaseModel):
    product: ProductRecord
    similarity_score: float
    retrieval_rank: int


class CandidateSet(BaseModel):
    schema_version: SchemaVersion = SchemaVersion.v1
    user_id: UUID
    candidates: list[CandidateItem]
    retrieval_latency_ms: float


class RankedItem(BaseModel):
    product: ProductRecord
    final_score: float
    rank: int
    score_breakdown: dict[str, float] = Field(default_factory=dict)


class FeedItem(BaseModel):
    product: ProductRecord
    final_score: float
    rank: int
    explanation_tags: list[str] = Field(default_factory=list)
    explanation_sentence: str | None = None
    price_ladder: list[dict[str, Any]] = Field(default_factory=list)


class FeedResult(BaseModel):
    schema_version: SchemaVersion = SchemaVersion.v1
    user_id: UUID
    items: list[FeedItem]
    trace: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

class ModuleTrace(BaseModel):
    module: str
    latency_ms: float
    warnings: list[str] = Field(default_factory=list)
    version: str | None = None
    fallback_used: bool = False
