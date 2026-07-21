from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends

from api.auth import get_current_user_id
from api.schemas import ProfilePatchRequest, ProfileResponse
from api.store import get_or_create_profile, save_profile

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
def get_profile(user_id: UUID = Depends(get_current_user_id)):
    profile = get_or_create_profile(user_id)
    return ProfileResponse(
        user_id=profile.user_id,
        hard_constraints=profile.hard_constraints,
        editable_preferences=profile.editable_preferences,
        event_count=profile.event_count,
        is_cold_start=profile.is_cold_start,
    )


@router.patch("", response_model=ProfileResponse)
def patch_profile(
    body: ProfilePatchRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    profile = get_or_create_profile(user_id)
    updates: dict = {"last_updated": datetime.now(timezone.utc)}
    if body.hard_constraints is not None:
        updates["hard_constraints"] = body.hard_constraints
    if body.editable_preferences is not None:
        updates["editable_preferences"] = body.editable_preferences
    updated = profile.model_copy(update=updates)
    save_profile(updated)
    return ProfileResponse(
        user_id=updated.user_id,
        hard_constraints=updated.hard_constraints,
        editable_preferences=updated.editable_preferences,
        event_count=updated.event_count,
        is_cold_start=updated.is_cold_start,
    )
