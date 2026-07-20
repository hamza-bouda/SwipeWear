from __future__ import annotations
from contracts.interfaces import FeedResult, UserPreferenceProfile

def explain(
    profile: UserPreferenceProfile,
    feed: FeedResult,
) -> FeedResult:
    # Annotate FeedItems with tags + sentence grounded in profile evidence only.
    # Pure function. Latency < 30 ms CPU. Fallback: editable tags, no sentence.
    raise NotImplementedError
