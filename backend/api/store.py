"""In-memory stores for MVP. Will be replaced by PostgreSQL + pgvector."""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from uuid import UUID

from contracts.events import InteractionEvent
from contracts.profile import UserPreferenceProfile


@dataclass
class UserRecord:
    user_id: UUID
    email: str
    password_hash: str


def _hash_password(password: str) -> str:
    salt = os.getenv("PASSWORD_SALT", "swipewear-dev-salt")
    return hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return _hash_password(password) == password_hash


_profiles: dict[UUID, UserPreferenceProfile] = {}
_events: list[InteractionEvent] = []
_users: dict[UUID, UserRecord] = {}
_email_index: dict[str, UUID] = {}


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


def create_user(user_id: UUID, email: str, password: str) -> UserRecord:
    record = UserRecord(
        user_id=user_id,
        email=email.lower(),
        password_hash=_hash_password(password),
    )
    _users[user_id] = record
    _email_index[email.lower()] = user_id
    return record


def get_user_by_email(email: str) -> UserRecord | None:
    uid = _email_index.get(email.lower())
    if uid is None:
        return None
    return _users.get(uid)


def get_user(user_id: UUID) -> UserRecord | None:
    return _users.get(user_id)


def delete_user(user_id: UUID) -> bool:
    user = _users.pop(user_id, None)
    if user is None:
        return False
    _email_index.pop(user.email, None)
    _profiles.pop(user_id, None)
    _events[:] = [e for e in _events if e.user_id != user_id]
    return True


def migrate_anonymous_profile(anonymous_id: UUID, new_id: UUID) -> bool:
    profile = _profiles.pop(anonymous_id, None)
    if profile is None:
        return False
    profile_data = profile.model_dump()
    profile_data["user_id"] = new_id
    _profiles[new_id] = UserPreferenceProfile(**profile_data)
    for event in _events:
        if event.user_id == anonymous_id:
            object.__setattr__(event, "user_id", new_id)
    return True


def reset() -> None:
    _profiles.clear()
    _events.clear()
    _users.clear()
    _email_index.clear()
