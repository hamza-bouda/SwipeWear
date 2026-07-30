from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from contracts.events import EventType
from contracts.pipeline import RankedItem
from contracts.product import Gender, ProductRecord
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


PreferenceAttribute = Literal[
    "liked_brands", "rejected_brands", "color", "category", "style",
    "max_price_eur", "sizes",
]


class PreferenceItem(BaseModel):
    id: str
    attribute: PreferenceAttribute
    value: str
    source: Literal["learned", "edited"]
    locked: bool = False


class PreferencesResponse(BaseModel):
    preferences: list[PreferenceItem]


class PreferenceMutationRequest(BaseModel):
    attribute: PreferenceAttribute
    value: str


class PreferenceMutationResponse(BaseModel):
    preference: PreferenceItem


class SavesResponse(BaseModel):
    products: list[ProductRecord] = Field(default_factory=list)


class OnboardingStylesRequest(BaseModel):
    style_ids: list[str] = Field(default_factory=list)
    liked_brands: list[str] = Field(default_factory=list)
    sizes: list[str] = Field(default_factory=list)
    max_price_eur: float | None = None
    gender: Gender | None = None


class OnboardingImagesRequest(BaseModel):
    image_urls: list[str] = Field(min_length=1)


class OnboardingResponse(BaseModel):
    user_id: UUID
    profile_initialized: bool = True


class AnonymousSessionResponse(BaseModel):
    """A browsing identity for someone with no account.

    The server generates the id. The previous endpoint took one from the
    request body and signed it unconditionally, so anyone who knew a user_id
    could mint a valid token for that account.
    """
    user_id: UUID
    access_token: str
    token_type: str = "bearer"


class SyncAccountRequest(BaseModel):
    """Sent once, right after a Supabase sign-in.

    `anonymous_user_id` carries over the profile built while browsing without
    an account; omitting it discards everything the visitor did before.
    """
    anonymous_user_id: UUID | None = None


class AuthUserResponse(BaseModel):
    user_id: UUID
    email: str | None = None
    provider: str = "unknown"
    profile_migrated: bool = False


class DeleteAccountResponse(BaseModel):
    deleted: bool = True
    user_id: UUID
