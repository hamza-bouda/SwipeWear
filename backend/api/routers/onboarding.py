from __future__ import annotations

import logging
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends

from api.auth import get_current_user_id
from api.schemas import (
    OnboardingImagesRequest,
    OnboardingResponse,
    OnboardingStylesRequest,
)
from api.store import get_or_create_profile, save_profile
from embeddings.fashionsiglip import get_service
from embeddings.indexer import download_image
from preferences.onboarding import build_profile_from_images, build_profile_from_styles

_LOG = logging.getLogger("swipewear.api.onboarding")

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.post("/styles", response_model=OnboardingResponse, status_code=201)
def post_onboarding_styles(
    body: OnboardingStylesRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    profile = get_or_create_profile(user_id)
    built = build_profile_from_styles(body.style_ids)
    new_prefs = profile.editable_preferences.model_copy(
        update={"liked_brands": body.liked_brands}
    )
    new_constraints = profile.hard_constraints.model_copy(
        update={
            "sizes": body.sizes,
            "max_price_eur": body.max_price_eur,
            # None leaves the existing choice alone: onboarding can be replayed
            # and must not silently clear a gender set from the settings screen.
            "gender": body.gender or profile.hard_constraints.gender,
        }
    )
    updated = profile.model_copy(
        update={
            "editable_preferences": new_prefs,
            "hard_constraints": new_constraints,
            "vectors": built.vectors,
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
    embedding_service = get_service()

    with tempfile.TemporaryDirectory() as tmp_dir:
        image_paths = []
        for index, url in enumerate(body.image_urls):
            try:
                data = download_image(url)
            except Exception as exc:  # noqa: BLE001 - one bad URL must not fail onboarding
                _LOG.warning("Skipping unreachable onboarding image %s: %s", url, exc)
                continue
            path = Path(tmp_dir) / f"onboarding-{index}"
            path.write_bytes(data)
            image_paths.append(str(path))

        built = build_profile_from_images(image_paths, embedding_service)

    updated = profile.model_copy(
        update={
            "vectors": built.vectors,
            "last_updated": datetime.now(timezone.utc),
        }
    )
    save_profile(updated)
    return OnboardingResponse(user_id=user_id)
