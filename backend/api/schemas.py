from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from contracts.events import EventType
from contracts.pipeline import RankedItem
from contracts.profile import EditablePreferences, HardConstraints


class FeedRequest(BaseModel):
    n_results: int = Field(default=30, ge=1, le=100)
    cursor: str | None = None


class FeedResponse(BaseModel):
    items: list[RankedItem]
    next_cursor: str | None = None
    fallback_used: bool = False


class EventRequest(BaseModel):
    product_id: str
    event_type: EventType
    payload: dict = Field(default_factory=dict)


class EventResponse(BaseModel):
    event_id: UUID
    accepted: bool = True


class ProfileResponse(BaseModel):
    user_id: UUID
    hard_constraints: HardConstraints
    editable_preferences: EditablePreferences
    event_count: int
    is_cold_start: bool


class ProfilePatchRequest(BaseModel):
    hard_constraints: HardConstraints | None = None
    editable_preferences: EditablePreferences | None = None


class OnboardingStylesRequest(BaseModel):
    liked_brands: list[str] = Field(default_factory=list)
    sizes: list[str] = Field(default_factory=list)
    max_price_eur: float | None = None


class OnboardingImagesRequest(BaseModel):
    image_urls: list[str] = Field(min_length=1)


class OnboardingResponse(BaseModel):
    user_id: UUID
    profile_initialized: bool = True


class TokenRequest(BaseModel):
    user_id: UUID


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
