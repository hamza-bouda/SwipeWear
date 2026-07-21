
from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from contracts.events import InteractionEvent
from contracts.profile import UserPreferenceProfile
from preferences.updater import PreferenceUpdater

_updater = PreferenceUpdater()


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
        profile = _updater.apply(profile, event)
    return profile
