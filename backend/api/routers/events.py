from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends

from api.auth import get_current_user_id
from api.schemas import EventRequest, EventResponse
from api.store import append_event, get_or_create_profile, save_profile
from contracts.events import EventType, InteractionEvent

router = APIRouter(prefix="/events", tags=["events"])


def _apply_event_to_profile(profile, event: InteractionEvent):
    """Minimal preference updater for MVP — adds liked/rejected brands."""
    updates: dict = {"event_count": profile.event_count + 1}

    if event.event_type == EventType.swipe_right:
        brand = event.payload.get("brand")
        if brand and brand not in profile.editable_preferences.liked_brands:
            new_liked = [*profile.editable_preferences.liked_brands, brand]
            new_prefs = profile.editable_preferences.model_copy(
                update={"liked_brands": new_liked}
            )
            updates["editable_preferences"] = new_prefs

    elif event.event_type == EventType.swipe_left_style:
        brand = event.payload.get("brand")
        if brand and brand not in profile.editable_preferences.rejected_brands:
            new_rejected = [*profile.editable_preferences.rejected_brands, brand]
            new_prefs = profile.editable_preferences.model_copy(
                update={"rejected_brands": new_rejected}
            )
            updates["editable_preferences"] = new_prefs

    updates["last_updated"] = datetime.now(timezone.utc)
    return profile.model_copy(update=updates)


@router.post("", response_model=EventResponse, status_code=201)
def post_event(
    body: EventRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    event = InteractionEvent(
        user_id=user_id,
        product_id=body.product_id,
        event_type=body.event_type,
        payload=body.payload,
    )
    append_event(event)

    profile = get_or_create_profile(user_id)
    updated = _apply_event_to_profile(profile, event)
    save_profile(updated)

    return EventResponse(event_id=event.event_id)
