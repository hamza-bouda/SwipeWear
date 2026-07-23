from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from api.auth import get_current_user_id
from api.schemas import EventRequest, EventResponse
from api.store import append_event, get_or_create_profile, save_profile
from contracts.events import InteractionEvent
from preferences.fallback_updater import FallbackUpdater

router = APIRouter(prefix="/events", tags=["events"])

_updater = FallbackUpdater()


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
    updated = _updater.apply(profile, event)
    save_profile(updated)

    return EventResponse(event_id=event.event_id)
