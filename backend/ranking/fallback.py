"""Ranking and policy fallbacks (blueprint SS12).

Ranker KO -> sort by retrieval similarity.
Policy KO  -> return ranked list as-is.
"""
from __future__ import annotations

import logging
from typing import Callable
from uuid import UUID

from contracts.pipeline import CandidateSet, RankedFeed, RankedItem
from contracts.profile import UserPreferenceProfile

_LOG = logging.getLogger("swipewear.ranking.fallback")


def similarity_fallback_rank(
    candidates: CandidateSet,
    user_id: UUID | None = None,
) -> RankedFeed:
    _LOG.warning(
        "Ranker fallback activated (user=%s): sorting by similarity",
        user_id,
    )
    sorted_candidates = sorted(
        candidates.candidates,
        key=lambda c: c.similarity_score,
        reverse=True,
    )
    items = [
        RankedItem(
            product=c.product,
            final_score=c.similarity_score,
            rank=rank,
            score_breakdown={"similarity": c.similarity_score},
        )
        for rank, c in enumerate(sorted_candidates, start=1)
    ]
    return RankedFeed(
        request_id=candidates.request_id,
        items=items,
        fallback_used=True,
    )


def rank_with_fallback(
    ranker_fn: Callable[[CandidateSet, UserPreferenceProfile], RankedFeed],
    candidates: CandidateSet,
    profile: UserPreferenceProfile,
) -> RankedFeed:
    try:
        return ranker_fn(candidates, profile)
    except Exception:
        _LOG.exception("Ranker failed, using similarity fallback")
        return similarity_fallback_rank(
            candidates, user_id=profile.user_id,
        )


def apply_policy_with_fallback(
    policy_fn: Callable[[RankedFeed], RankedFeed],
    ranked_feed: RankedFeed,
    user_id: UUID | None = None,
) -> RankedFeed:
    try:
        return policy_fn(ranked_feed)
    except Exception:
        _LOG.exception(
            "Policy fallback activated (user=%s): returning ranked list as-is",
            user_id,
        )
        return ranked_feed.model_copy(update={"fallback_used": True})
