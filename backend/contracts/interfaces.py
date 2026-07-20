"""
Shared contracts — Pydantic schemas used by every module.

CHANGELOG_contracts.md must be updated for any breaking change.
Every schema carries a schema_version field.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SchemaVersion(str, Enum):
    v1 = "1.0"


# ---------------------------------------------------------------------------
# Interaction events (source of truth for profile updates)
# ---------------------------------------------------------------------------

class SwipeDirection(str, Enum):
    right = "right"
    left_style = "left_style"
    left_price = "left_price"


class InteractionEvent(BaseModel):
    schema_version: SchemaVersion = SchemaVersion.v1
    event_id: UUID
    user_id: UUID
    product_id: str
    action: SwipeDirection | str
    timestamp: datetime
    session_id: UUID
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# User preference profile
# ---------------------------------------------------------------------------

class HardConstraints(BaseModel):
    sizes: list[str] = Field(default_factory=list)
    max_price_eur: float | None = None
    regions: list[str] = Field(default_factory=list)


class StyleVector(BaseModel):
    embedding_version: str = "fashionsiglip-v1"
    vector_dim: int = 512
    values: list[float]


class UserPreferenceProfile(BaseModel):
    schema_version: SchemaVersion = SchemaVersion.v1
    user_id: UUID
    hard_constraints: HardConstraints = Field(default_factory=HardConstraints)
    style_vector: StyleVector | None = None
    attribute_weights: dict[str, float] = Field(default_factory=dict)
    negative_evidence: list[str] = Field(default_factory=list)
    last_updated: datetime
    event_count: int = 0


# ---------------------------------------------------------------------------
# Product catalogue
# ---------------------------------------------------------------------------

class ProductCondition(str, Enum):
    new = "new"
    like_new = "like_new"
    good = "good"
    fair = "fair"


class ProductRecord(BaseModel):
    schema_version: SchemaVersion = SchemaVersion.v1
    product_id: str
    source: str
    title: str
    brand: str | None = None
    model: str | None = None
    size: str | None = None
    color: str | None = None
    condition: ProductCondition | None = None
    price_eur: float
    url: str
    affiliate_url: str | None = None
    image_urls: list[str] = Field(default_factory=list)
    embedding_version: str | None = None
    embedding: list[float] | None = None


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
