"""Preference updater -- one rule per InteractionEvent type (KAN-32, blueprint SS6).

Each event moves exactly one axis of the profile:
- swipe_right / save / open  -> vectors.positive (taste evidence)
- swipe_left_style           -> vectors.negative (negative style evidence)
- swipe_left_price           -> hard_constraints.max_price_eur ONLY
- edit_preference            -> editable_preferences (explicit override)

swipe_left_price must never touch the style vectors: mixing a price
complaint into taste evidence would poison the profile with an unrelated
signal (this is the AC's "critical test").

Note (brand weight / session intent -- a confirmer): the AC asks for
swipe_right to also carry "poids de marque et intent de session", but
neither InteractionEvent nor EditablePreferences has a dedicated field for
either. Implemented here as a best-effort interpretation -- brand from
event.payload["brand"] is added to liked_brands, and an optional
event.payload["session_intent_weight"] multiplies alpha -- pending
confirmation with the team.
"""
from __future__ import annotations

from math import sqrt
from typing import Any, Callable

from contracts.events import EventType, InteractionEvent
from contracts.profile import UserPreferenceProfile
from preferences.config import ALPHA, ALPHA_STRONG, BETA, PRICE_DISCOUNT


def _l2_normalize(vector: list[float]) -> list[float]:
    norm = sqrt(sum(v * v for v in vector))
    if norm == 0.0:
        return vector
    return [v / norm for v in vector]


def _accumulate(vector: list[float], embedding: list[float], weight: float) -> list[float]:
    if not vector:
        vector = [0.0] * len(embedding)
    updated = [v + weight * e for v, e in zip(vector, embedding)]
    return _l2_normalize(updated)


def _weighted_alpha(event: InteractionEvent, base_alpha: float) -> float:
    return base_alpha * float(event.payload.get("session_intent_weight", 1.0))


def _apply_positive_signal(data: dict[str, Any], event: InteractionEvent, alpha: float) -> None:
    embedding = event.payload.get("product_embedding")
    if embedding:
        weight = _weighted_alpha(event, alpha)
        data["vectors"]["positive"] = _accumulate(
            data["vectors"]["positive"], embedding, weight,
        )

    brand = event.payload.get("brand")
    liked_brands = data["editable_preferences"]["liked_brands"]
    if brand and brand not in liked_brands:
        liked_brands.append(brand)


def _apply_negative_style_signal(data: dict[str, Any], event: InteractionEvent) -> None:
    embedding = event.payload.get("product_embedding")
    if not embedding:
        return
    data["vectors"]["negative"] = _accumulate(
        data["vectors"]["negative"], embedding, BETA,
    )


def _apply_price_signal(data: dict[str, Any], event: InteractionEvent) -> None:
    price = event.payload.get("product_price_eur")
    if price is None:
        return
    candidate = float(price) * PRICE_DISCOUNT
    current = data["hard_constraints"]["max_price_eur"]
    data["hard_constraints"]["max_price_eur"] = (
        candidate if current is None else min(current, candidate)
    )


def _apply_edit_preference(data: dict[str, Any], event: InteractionEvent) -> None:
    field = event.payload.get("field")
    value = event.payload.get("value")
    if field is None or value is None:
        return

    if field == "liked_brands":
        if value not in data["editable_preferences"]["liked_brands"]:
            data["editable_preferences"]["liked_brands"].append(value)
    elif field == "rejected_brands":
        if value not in data["editable_preferences"]["rejected_brands"]:
            data["editable_preferences"]["rejected_brands"].append(value)
    elif field == "max_price_eur":
        data["hard_constraints"]["max_price_eur"] = float(value)


_HANDLERS: dict[EventType, Callable[[dict[str, Any], InteractionEvent], None]] = {
    EventType.swipe_right: lambda data, event: _apply_positive_signal(data, event, ALPHA),
    EventType.save: lambda data, event: _apply_positive_signal(data, event, ALPHA_STRONG),
    EventType.open: lambda data, event: _apply_positive_signal(data, event, ALPHA_STRONG),
    EventType.swipe_left_style: _apply_negative_style_signal,
    EventType.swipe_left_price: _apply_price_signal,
    EventType.edit_preference: _apply_edit_preference,
}


class PreferenceUpdater:
    """Applies a single InteractionEvent to a UserPreferenceProfile (pure function)."""

    def apply(
        self,
        profile: UserPreferenceProfile,
        event: InteractionEvent,
    ) -> UserPreferenceProfile:
        data = profile.model_dump()
        data["event_count"] += 1
        data["last_updated"] = event.timestamp

        handler = _HANDLERS.get(event.event_type)
        if handler is not None:
            handler(data, event)

        return UserPreferenceProfile(**data)
