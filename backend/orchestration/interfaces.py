from __future__ import annotations
from uuid import UUID
from contracts.interfaces import FeedResult, InteractionEvent

async def run_recommendation_pipeline(user_id: UUID) -> FeedResult:
    # Sequences: get_profile -> retrieve -> rank -> policy -> explain.
    # Total latency target < 300 ms CPU. No logic here — only call ordering.
    raise NotImplementedError

async def handle_interaction(event: InteractionEvent) -> None:
    # Persist event to log, then call preferences.apply_event.
    # Event log is source of truth — never update profile directly.
    raise NotImplementedError
