from __future__ import annotations
from contracts.interfaces import CandidateSet, RankedItem, UserPreferenceProfile

def rank_candidates(
    profile: UserPreferenceProfile,
    candidates: CandidateSet,
) -> list[RankedItem]:
    # Pure function — no I/O, no DB reads. Latency < 50 ms CPU. Fallback: order by similarity.
    # LightGBM ranker is frozen until real interaction data exists (see CLAUDE.md).
    raise NotImplementedError
