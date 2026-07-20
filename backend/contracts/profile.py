from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


SCHEMA_VERSION = 1


# ─────────────────────────────────────────────────────────────────────────────
# Layer 1 — Hard constraints (filtering, non-negotiable)
# Applied before any retrieval — products that violate these never appear.
# ─────────────────────────────────────────────────────────────────────────────

class HardConstraints(BaseModel):
    sizes: list[str] = Field(default_factory=list)
    max_price_eur: float | None = None
    regions: list[str] = Field(default_factory=list)
    excluded_conditions: list[str] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Layer 2 — Editable preferences (inspectable, user-controllable)
# Displayed in "Your Algorithm" and modifiable without a swipe.
# ─────────────────────────────────────────────────────────────────────────────

class LockedAttribute(BaseModel):
    attribute: str
    value: str
    weight: float = 1.0


class EditablePreferences(BaseModel):
    liked_brands: list[str] = Field(default_factory=list)
    rejected_brands: list[str] = Field(default_factory=list)
    locked_attributes: list[LockedAttribute] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Layer 3 — Dense vectors (learned from swipes + inspiration images)
# Used by retrieval (ANN) and ranking (cosine similarity).
# ─────────────────────────────────────────────────────────────────────────────

class StyleVectors(BaseModel):
    positive: list[float] = Field(default_factory=list)
    negative: list[float] = Field(default_factory=list)
    embedding_version: str = "fashionsiglip-v1"
    vector_dim: int = 512


# ─────────────────────────────────────────────────────────────────────────────
# Root profile — passed whole to ranking (no hidden DB reads, blueprint §11)
# ─────────────────────────────────────────────────────────────────────────────

class UserPreferenceProfile(BaseModel):
    user_id: UUID = Field(default_factory=uuid4)
    schema_version: int = SCHEMA_VERSION
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    event_count: int = 0

    # The three layers
    hard_constraints: HardConstraints = Field(default_factory=HardConstraints)
    editable_preferences: EditablePreferences = Field(
        default_factory=EditablePreferences
    )
    vectors: StyleVectors = Field(default_factory=StyleVectors)

    @property
    def is_cold_start(self) -> bool:
        return self.event_count == 0 and not self.vectors.positive
