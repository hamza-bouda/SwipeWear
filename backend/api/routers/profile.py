from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from api.auth import get_current_user_id
from api.schemas import (
    PreferenceItem,
    PreferenceMutationRequest,
    PreferenceMutationResponse,
    PreferencesResponse,
    ProfilePatchRequest,
    ProfileResponse,
)
from api.store import append_event, get_or_create_profile, save_profile
from contracts.events import EventType, InteractionEvent
from contracts.profile import LockedAttribute, UserPreferenceProfile

router = APIRouter(prefix="/profile", tags=["profile"])


def _is_locked(profile: UserPreferenceProfile, attribute: str, value: str) -> bool:
    aliases = {attribute}
    if attribute in {"liked_brands", "rejected_brands"}:
        aliases.add("brand")
    return any(
        item.locked and item.attribute in aliases and item.value == value
        for item in profile.editable_preferences.locked_attributes
    )


def _item(attribute: str, value: str, source: str, locked: bool) -> PreferenceItem:
    return PreferenceItem(
        id=f"{attribute}:{value}", attribute=attribute, value=value,
        source=source, locked=locked,
    )


def _items(profile: UserPreferenceProfile) -> list[PreferenceItem]:
    preferences: list[PreferenceItem] = []
    editable = profile.editable_preferences
    for brand in editable.liked_brands:
        preferences.append(_item(
            "liked_brands", brand, "edited", _is_locked(profile, "liked_brands", brand),
        ))
    for brand in editable.rejected_brands:
        preferences.append(_item(
            "rejected_brands", brand, "edited", _is_locked(profile, "rejected_brands", brand),
        ))
    if profile.hard_constraints.max_price_eur is not None:
        value = str(profile.hard_constraints.max_price_eur)
        preferences.append(_item(
            "max_price_eur", value, "edited", _is_locked(profile, "max_price_eur", value),
        ))
    for size in profile.hard_constraints.sizes:
        preferences.append(_item("sizes", size, "edited", _is_locked(profile, "sizes", size)))
    for learned in editable.locked_attributes:
        if learned.attribute in {"color", "category", "style"}:
            preferences.append(_item(
                learned.attribute, learned.value, "learned", learned.locked,
            ))
    return preferences


def _event(user_id: UUID, action: str, attribute: str, value: str) -> InteractionEvent:
    event = InteractionEvent(
        user_id=user_id,
        product_id="profile",
        event_type=EventType.edit_preference,
        payload={"action": action, "field": attribute, "value": value},
    )
    append_event(event)
    return event


def _find(preference_id: str, profile: UserPreferenceProfile) -> PreferenceItem:
    for item in _items(profile):
        if item.id == preference_id:
            return item
    raise HTTPException(status_code=404, detail="Preference not found")


def _save(profile: UserPreferenceProfile, updates: dict) -> UserPreferenceProfile:
    updated = profile.model_copy(update={
        **updates,
        "event_count": profile.event_count + 1,
        "last_updated": datetime.now(timezone.utc),
    })
    save_profile(updated)
    return updated


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


@router.get("/preferences", response_model=PreferencesResponse)
def get_preferences(user_id: UUID = Depends(get_current_user_id)):
    return PreferencesResponse(preferences=_items(get_or_create_profile(user_id)))


@router.post("/preferences", response_model=PreferenceMutationResponse, status_code=201)
def add_preference(
    body: PreferenceMutationRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    profile = get_or_create_profile(user_id)
    value = body.value.strip()
    if not value:
        raise HTTPException(status_code=422, detail="Preference value is required")
    if body.attribute == "liked_brands":
        prefs = profile.editable_preferences.model_copy(update={
            "liked_brands": list(dict.fromkeys([
                *profile.editable_preferences.liked_brands, value,
            ])),
        })
        updated = _save(profile, {"editable_preferences": prefs})
    elif body.attribute == "rejected_brands":
        prefs = profile.editable_preferences.model_copy(update={
            "rejected_brands": list(dict.fromkeys([
                *profile.editable_preferences.rejected_brands, value,
            ])),
        })
        updated = _save(profile, {"editable_preferences": prefs})
    elif body.attribute == "max_price_eur":
        try:
            budget = float(value)
        except ValueError as exc:
            raise HTTPException(
                status_code=422, detail="Budget must be numeric",
            ) from exc
        constraints = profile.hard_constraints.model_copy(
            update={"max_price_eur": budget},
        )
        updated = _save(profile, {"hard_constraints": constraints})
    elif body.attribute == "sizes":
        sizes = list(dict.fromkeys([*profile.hard_constraints.sizes, value]))
        constraints = profile.hard_constraints.model_copy(update={"sizes": sizes})
        updated = _save(profile, {"hard_constraints": constraints})
    else:
        attrs = [*profile.editable_preferences.locked_attributes]
        if not any(
            item.attribute == body.attribute and item.value == value
            for item in attrs
        ):
            attrs.append(LockedAttribute(
                attribute=body.attribute, value=value, weight=0.0,
            ))
        prefs = profile.editable_preferences.model_copy(
            update={"locked_attributes": attrs},
        )
        updated = _save(profile, {"editable_preferences": prefs})
    _event(user_id, "add", body.attribute, value)
    return PreferenceMutationResponse(
        preference=_find(f"{body.attribute}:{value}", updated),
    )


@router.delete("/preferences/{preference_id}", status_code=204)
def delete_preference(
    preference_id: str, user_id: UUID = Depends(get_current_user_id),
):
    profile = get_or_create_profile(user_id)
    item = _find(preference_id, profile)
    prefs = profile.editable_preferences
    if item.attribute == "liked_brands":
        values = [x for x in prefs.liked_brands if x != item.value]
        _save(profile, {"editable_preferences": prefs.model_copy(
            update={"liked_brands": values},
        )})
    elif item.attribute == "rejected_brands":
        values = [x for x in prefs.rejected_brands if x != item.value]
        _save(profile, {"editable_preferences": prefs.model_copy(
            update={"rejected_brands": values},
        )})
    elif item.attribute == "sizes":
        values = [x for x in profile.hard_constraints.sizes if x != item.value]
        _save(profile, {"hard_constraints": profile.hard_constraints.model_copy(
            update={"sizes": values},
        )})
    elif item.attribute == "max_price_eur":
        constraints = profile.hard_constraints.model_copy(
            update={"max_price_eur": None},
        )
        _save(profile, {"hard_constraints": constraints})
    else:
        attrs = [x for x in prefs.locked_attributes if not (
            x.attribute == item.attribute and x.value == item.value
        )]
        _save(profile, {"editable_preferences": prefs.model_copy(
            update={"locked_attributes": attrs},
        )})
    _event(user_id, "delete", item.attribute, item.value)
    return None


def _set_lock(preference_id: str, user_id: UUID, locked: bool) -> PreferenceMutationResponse:
    profile = get_or_create_profile(user_id)
    item = _find(preference_id, profile)
    lock_attribute = (
        "brand" if item.attribute in {"liked_brands", "rejected_brands"}
        else item.attribute
    )
    attrs = [*profile.editable_preferences.locked_attributes]
    matching = next(
        (x for x in attrs if x.attribute == lock_attribute and x.value == item.value),
        None,
    )
    if matching is None:
        attrs.append(LockedAttribute(
            attribute=lock_attribute, value=item.value, locked=locked,
        ))
    else:
        attrs[attrs.index(matching)] = matching.model_copy(update={"locked": locked})
    prefs = profile.editable_preferences.model_copy(
        update={"locked_attributes": attrs},
    )
    updated = _save(profile, {"editable_preferences": prefs})
    _event(user_id, "lock" if locked else "unlock", item.attribute, item.value)
    return PreferenceMutationResponse(preference=_find(preference_id, updated))


@router.post("/preferences/{preference_id}/lock", response_model=PreferenceMutationResponse)
def lock_preference(preference_id: str, user_id: UUID = Depends(get_current_user_id)):
    return _set_lock(preference_id, user_id, True)


@router.post("/preferences/{preference_id}/unlock", response_model=PreferenceMutationResponse)
def unlock_preference(preference_id: str, user_id: UUID = Depends(get_current_user_id)):
    return _set_lock(preference_id, user_id, False)
