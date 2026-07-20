from __future__ import annotations

from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from contracts.product import ProductRecord
from contracts.profile import UserPreferenceProfile


SCHEMA_VERSION = 1


# ── RecoRequest — pipeline entry point ───────────────────────────────────────

class RecoRequest(BaseModel):
    request_id: UUID = Field(default_factory=uuid4)
    user_profile: UserPreferenceProfile
    n_results: int = 30
    session_intent: str | None = None   # e.g. "casual", "sport", "work"
    schema_version: int = SCHEMA_VERSION


# ── CandidateSet — retrieval output → ranking input ──────────────────────────

class CandidateItem(BaseModel):
    product: ProductRecord
    similarity_score: float
    retrieval_rank: int


class CandidateSet(BaseModel):
    request_id: UUID
    candidates: list[CandidateItem]
    hard_filters_applied: list[str] = Field(default_factory=list)
    retrieval_latency_ms: float = 0.0
    fallback_used: bool = False
    schema_version: int = SCHEMA_VERSION


# ── RankedFeed — ranking+policy output → explainer input ─────────────────────

class PriceLadderEntry(BaseModel):
    url: str
    price_eur: float
    source: str
    is_new: bool = False
    affiliate_url: str | None = None


class RankedItem(BaseModel):
    product: ProductRecord
    final_score: float
    rank: int
    score_breakdown: dict[str, float] = Field(default_factory=dict)
    price_ladder: list[PriceLadderEntry] = Field(default_factory=list)


class RankedFeed(BaseModel):
    request_id: UUID
    items: list[RankedItem]
    diversity_applied: bool = False
    ranking_latency_ms: float = 0.0
    fallback_used: bool = False
    schema_version: int = SCHEMA_VERSION


# ── Explanation — explainer output → API response ────────────────────────────

class Explanation(BaseModel):
    product_id: str
    reasons: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    grounded: bool = False
    editable_tags: list[str] = Field(default_factory=list)
    sentence: str | None = None
    schema_version: int = SCHEMA_VERSION


# ── ModuleTrace — observability ──────────────────────────────────────────────

class ModuleTrace(BaseModel):
    module: str
    latency_ms: float
    warnings: list[str] = Field(default_factory=list)
    version: str | None = None
    fallback_used: bool = False
