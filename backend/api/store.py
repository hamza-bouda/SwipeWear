"""In-memory stores for MVP. Will be replaced by PostgreSQL + pgvector."""
from __future__ import annotations

from uuid import UUID

from contracts.events import InteractionEvent
from contracts.profile import UserPreferenceProfile


_profiles: dict[UUID, UserPreferenceProfile] = {}
_events: list[InteractionEvent] = []


def get_or_create_profile(user_id: UUID) -> UserPreferenceProfile:
    if user_id not in _profiles:
        _profiles[user_id] = UserPreferenceProfile(user_id=user_id)
    return _profiles[user_id]


def save_profile(profile: UserPreferenceProfile) -> None:
    _profiles[profile.user_id] = profile


def append_event(event: InteractionEvent) -> None:
    _events.append(event)


def get_events_for_user(user_id: UUID) -> list[InteractionEvent]:
    return [e for e in _events if e.user_id == user_id]


def reset() -> None:
    _profiles.clear()
    _events.clear()
