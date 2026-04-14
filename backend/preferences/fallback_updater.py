"""Fallback preference updater — blueprint §12.

If PreferenceUpdater.apply() raises, the profile is returned with
event_count incremented (not completely frozen) and the failed event is
queued for automatic replay on the next successful call for that user.

Queue is in-process and non-persistent (post-MVP: DB-backed queue).
Replay is attempted on top of the live profile, preserving all prior state.
"""
from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from uuid import UUID

from contracts.events import InteractionEvent
from contracts.profile import UserPreferenceProfile
from preferences.updater import PreferenceUpdater

_LOG = logging.getLogger("swipewear.preferences.fallback_updater")


class FallbackUpdater:
    """PreferenceUpdater with a degraded-mode fallback (blueprint §12).

    On failure:
    - Returns the profile with event_count + 1 (event is not silently lost)
    - Queues the failed event; it will be replayed on the next apply() call
      for the same user once the underlying updater recovers.
    """

    def __init__(self) -> None:
        self._inner = PreferenceUpdater()
        self._queue: list[tuple[str, InteractionEvent]] = []
        self._lock = threading.Lock()

    def apply(
        self,
        profile: UserPreferenceProfile,
        event: InteractionEvent,
    ) -> UserPreferenceProfile:
        uid_str = str(profile.user_id)

        # Recovery path: replay any previously queued events for this user.
        queued = self._pop_user_queue(uid_str)
        if queued:
            _LOG.info(
                "Replaying %d queued events for user %s",
                len(queued), uid_str,
            )
            for queued_event in sorted(queued, key=lambda e: e.timestamp):
                try:
                    profile = self._inner.apply(profile, queued_event)
                except Exception:
                    _LOG.warning(
                        "Queued event replay failed for user %s — requeueing",
                        uid_str, exc_info=True,
                    )
                    with self._lock:
                        self._queue.append((uid_str, queued_event))

        # Apply the current event.
        try:
            return self._inner.apply(profile, event)
        except Exception:
            _LOG.warning(
                "PreferenceUpdater.apply() failed for user %s event_type=%s"
                " — degraded mode, event queued for replay",
                uid_str, event.event_type, exc_info=True,
            )
            with self._lock:
                self._queue.append((uid_str, event))
            return profile.model_copy(update={
                "event_count": profile.event_count + 1,
                "last_updated": datetime.now(timezone.utc),
            })

    def _pop_user_queue(self, uid_str: str) -> list[InteractionEvent]:
        with self._lock:
            events = [e for uid, e in self._queue if uid == uid_str]
            self._queue = [(uid, e) for uid, e in self._queue if uid != uid_str]
        return events

    def queue_size(self) -> int:
        """Number of events pending replay (0 = fully healthy)."""
        with self._lock:
            return len(self._queue)

    def drain_queue(self) -> list[InteractionEvent]:
        """Return and clear all queued events (for monitoring or testing)."""
        with self._lock:
            events = [e for _, e in self._queue]
            self._queue.clear()
        return events
