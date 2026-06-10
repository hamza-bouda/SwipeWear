from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends

from api.auth import get_current_user_id
from api.schemas import (
    OnboardingImagesRequest,
    OnboardingResponse,
    OnboardingStylesRequest,
)
from api.store import get_or_create_profile, save_profile

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.post("/styles", response_model=OnboardingResponse, status_code=201)
def post_onboarding_styles(
    body: OnboardingStylesRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    profile = get_or_create_profile(user_id)
    new_prefs = profile.editable_preferences.model_copy(
        update={"liked_brands": body.liked_brands}
    )
    new_constraints = profile.hard_constraints.model_copy(
        update={
            "sizes": body.sizes,
            "max_price_eur": body.max_price_eur,
        }
    )
    updated = profile.model_copy(
        update={
            "editable_preferences": new_prefs,
            "hard_constraints": new_constraints,
            "last_updated": datetime.now(timezone.utc),
        }
    )
    save_profile(updated)
    return OnboardingResponse(user_id=user_id)


@router.post("/images", response_model=OnboardingResponse, status_code=201)
def post_onboarding_images(
    body: OnboardingImagesRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    profile = get_or_create_profile(user_id)
    updated = profile.model_copy(
        update={"last_updated": datetime.now(timezone.utc)}
    )
    save_profile(updated)
    return OnboardingResponse(user_id=user_id)
