"""Contracts for one observable recommendation request."""
from __future__ import annotations

from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from contracts.pipeline import ModuleTrace


class RequestTrace(BaseModel):
    """An immutable-shaped record of every pipeline stage for one feed request."""

    trace_id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    modules: list[ModuleTrace] = Field(default_factory=list)
    total_latency_ms: float = 0.0
    schema_version: int = 1

