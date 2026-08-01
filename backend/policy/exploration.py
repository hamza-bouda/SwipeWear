"""Epsilon-greedy exploration — break the taste bubble (blueprint SS8)."""
from __future__ import annotations

import logging
import random

from contracts.pipeline import RankedFeed, RankedItem
from contracts.product import ProductRecord

_LOG = logging.getLogger("swipewear.policy.exploration")

EXPLORATION_MARKER = "exploration"


def epsilon_greedy_inject(
    feed: RankedFeed,
    catalogue_sample: list[ProductRecord],
    epsilon: float = 0.15,
    rng: random.Random | None = None,
) -> RankedFeed:
    if not feed.items or epsilon <= 0.0 or not catalogue_sample:
        return feed

    rng = rng or random.Random()

    existing_ids = {it.product.id for it in feed.items}
    pool = [p for p in catalogue_sample if p.id not in existing_ids]
    if not pool:
        return feed

    new_items: list[RankedItem] = []
    pool_idx = 0
    rng.shuffle(pool)

    for item in feed.items:
        if rng.random() < epsilon and pool_idx < len(pool):
            explore_product = pool[pool_idx]
            pool_idx += 1
            new_items.append(
                RankedItem(
                    product=explore_product,
                    final_score=0.0,
                    rank=0,
                    score_breakdown={EXPLORATION_MARKER: 1.0},
                ),
            )
        else:
            new_items.append(item)

    for i, item in enumerate(new_items, start=1):
        new_items[i - 1] = item.model_copy(update={"rank": i})

    n_explore = sum(
        1 for it in new_items
        if it.score_breakdown.get(EXPLORATION_MARKER, 0.0) > 0
    )
    _LOG.info(
        "Epsilon-greedy: injected %d/%d exploration items (epsilon=%.2f)",
        n_explore, len(new_items), epsilon,
    )

    return feed.model_copy(update={"items": new_items})
