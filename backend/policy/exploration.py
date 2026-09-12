"""Epsilon-greedy exploration — break the taste bubble (blueprint SS8)."""
from __future__ import annotations

import logging
import random

from contracts.pipeline import RankedFeed, RankedItem
from contracts.product import ProductRecord

_LOG = logging.getLogger("swipewear.policy.exploration")

EXPLORATION_MARKER = "exploration"
FRESHNESS_24H_MARKER = "freshness_24h"


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


def compose_feed(
    feed: RankedFeed,
    limit: int,
) -> RankedFeed:
    """Compose the visible page according to the product rule F06.

    The ranker and epsilon injector deliberately over-fetch. This final
    selection is where the user-visible page gets its 70% exploitation, 15%
    exploration and 15% freshness mix. If one bucket is unavailable (for
    example a small catalogue has no listing younger than 24 hours), its slots
    are filled from the other buckets instead of returning a short feed.
    """
    if limit <= 0 or not feed.items:
        return feed.model_copy(update={"items": []})

    page_size = min(limit, len(feed.items))
    exploitation: list[RankedItem] = []
    exploration: list[RankedItem] = []
    freshness: list[RankedItem] = []

    for item in feed.items:
        if item.score_breakdown.get(EXPLORATION_MARKER, 0.0) > 0:
            exploration.append(item)
        elif item.score_breakdown.get(FRESHNESS_24H_MARKER, 0.0) > 0:
            freshness.append(item)
        else:
            exploitation.append(item)

    # Use floor for the two explicit 15% buckets and give the rounding
    # remainder to freshness. For a 30-card page this is 21 / 4 / 5.
    target_exploitation = int(page_size * 0.70)
    target_exploration = int(page_size * 0.15)
    target_freshness = page_size - target_exploitation - target_exploration

    selected = (
        exploitation[:target_exploitation]
        + exploration[:target_exploration]
        + freshness[:target_freshness]
    )
    selected_ids = {item.product.id for item in selected}

    # A missing bucket must not make the deck smaller. Keep the original
    # ranking order as the deterministic fill order.
    for item in feed.items:
        if len(selected) >= page_size:
            break
        if item.product.id not in selected_ids:
            selected.append(item)
            selected_ids.add(item.product.id)

    selected = [
        item.model_copy(update={"rank": rank})
        for rank, item in enumerate(selected[:page_size], start=1)
    ]
    _LOG.info(
        "Feed composition: %d exploitation, %d exploration, %d freshness",
        sum(1 for item in selected if item.product.id in {x.product.id for x in exploitation}),
        sum(1 for item in selected if item.product.id in {x.product.id for x in exploration}),
        sum(1 for item in selected if item.product.id in {x.product.id for x in freshness}),
    )
    return feed.model_copy(update={"items": selected})
