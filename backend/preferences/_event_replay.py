
from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from contracts.events import EventType, InteractionEvent
from contracts.profile import UserPreferenceProfile


def _apply_event(
    profile: UserPreferenceProfile,
    event: InteractionEvent,
) -> UserPreferenceProfile:
    data = profile.model_dump()
    data["event_count"] += 1
    data["last_updated"] = event.timestamp
    prefs = data["editable_preferences"]
    hc = data["hard_constraints"]

    if event.event_type == EventType.edit_preference:
        field = event.payload.get("field")
        value = event.payload.get("value")
        if field == "liked_brands" and value:
            if value not in prefs["liked_brands"]:
                prefs["liked_brands"].append(value)
        elif field == "rejected_brands" and value:
            if value not in prefs["rejected_brands"]:
                prefs["rejected_brands"].append(value)
        elif field == "max_price_eur" and value is not None:
            hc["max_price_eur"] = float(value)

    elif event.event_type == EventType.swipe_left_price:
        product_price = event.payload.get("product_price_eur")
        if product_price is not None:
            current = hc.get("max_price_eur")
            if current is None or float(product_price) < current:
                hc["max_price_eur"] = float(product_price)

    return UserPreferenceProfile(**data)


def replay_events_in_memory(
    events: list[InteractionEvent],
    user_id: UUID | None = None,
    until: datetime | None = None,
) -> UserPreferenceProfile:
    filtered = sorted(events, key=lambda e: e.timestamp)
    if user_id:
        filtered = [e for e in filtered if e.user_id == user_id]
    if until:
        filtered = [e for e in filtered if e.timestamp <= until]

    uid = user_id or (filtered[0].user_id if filtered else uuid4())
    profile = UserPreferenceProfile(user_id=uid)
    for event in filtered:
        profile = _apply_event(profile, event)
    return profile
