"""Hard filters applied BEFORE vector search (blueprint SS8).

Diagnostic: symptom "wrong size or wrong price" -> look here.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from contracts.product import ProductRecord
from contracts.profile import HardConstraints, UserPreferenceProfile

_LOG = logging.getLogger("swipewear.retrieval.filters")

REGION_SOURCE_MAP: dict[str, list[str]] = {
    "FR": ["ebay", "awin", "cj"],
    "DE": ["ebay", "awin"],
    "UK": ["ebay", "awin", "cj"],
    "US": ["ebay", "cj"],
}


@dataclass
class HardFilterResult:
    clauses: list[str] = field(default_factory=list)
    params: dict[str, object] = field(default_factory=dict)
    applied: list[str] = field(default_factory=list)

    @property
    def where_sql(self) -> str:
        if not self.clauses:
            return ""
        return "WHERE " + " AND ".join(self.clauses)


def apply_hard_filters(
    profile: UserPreferenceProfile,
    blocked_sources: list[str] | None = None,
) -> HardFilterResult:
    hc = profile.hard_constraints
    clauses: list[str] = []
    params: dict[str, object] = {}
    applied: list[str] = []

    clauses.append("available = true")
    applied.append("available")

    if blocked_sources:
        clauses.append("source != ALL(%(filter_blocked_sources)s)")
        params["filter_blocked_sources"] = blocked_sources
        applied.append("watcher_kill_switch")

    if hc.gender is not None:
        # Show the shopper's gender, plus unisex and anything unrecorded.
        # 'unisex' is a real value that belongs in every feed, and 22 443 of
        # 50 927 products state no gender at all — excluding those would throw
        # away nearly half the catalogue to enforce a guess.
        clauses.append(
            "(gender IS NULL OR gender = ANY(%(filter_genders)s))"
        )
        params["filter_genders"] = [hc.gender.value, "unisex"]
        applied.append("gender")

    if hc.sizes:
        # An unknown size is not a wrong size. eBay's item summaries almost
        # never carry one: 43 of 50 870 ingested products have size_eu set, so
        # a strict `size_eu = ANY(...)` cut a 50 000-product catalogue down to
        # 15 matches and the feed ran dry after a single screen of swipes.
        # Products whose size is unrecorded are kept — the listing itself
        # states it — and the filter still excludes a known mismatch.
        clauses.append(
            "(size_eu IS NULL OR size_eu = ANY(%(filter_sizes)s))"
        )
        params["filter_sizes"] = hc.sizes
        applied.append("size")

    if hc.max_price_eur is not None:
        clauses.append("price <= %(filter_max_price)s")
        params["filter_max_price"] = hc.max_price_eur
        applied.append("max_price")

    if hc.regions:
        allowed: set[str] = set()
        for region in hc.regions:
            allowed.update(REGION_SOURCE_MAP.get(region, []))
        if allowed:
            clauses.append("source = ANY(%(filter_sources)s)")
            params["filter_sources"] = sorted(allowed)
            applied.append("region")

    if hc.excluded_conditions:
        clauses.append("NOT (condition = ANY(%(filter_excluded_cond)s))")
        params["filter_excluded_cond"] = hc.excluded_conditions
        applied.append("excluded_conditions")

    return HardFilterResult(clauses=clauses, params=params, applied=applied)


def matches_hard_filters(
    product: ProductRecord,
    constraints: HardConstraints,
) -> bool:
    if not product.available:
        return False

    if (
        constraints.gender is not None
        and product.gender is not None
        and product.gender.value not in (constraints.gender.value, "unisex")
    ):
        return False

    # Same rule as the SQL clause above: an unrecorded size is kept, a known
    # mismatch is dropped. The two must agree or the in-memory path would
    # reject candidates the query deliberately let through.
    if (
        constraints.sizes
        and product.size_eu is not None
        and product.size_eu not in constraints.sizes
    ):
        return False

    if (
        constraints.max_price_eur is not None
        and product.price > constraints.max_price_eur
    ):
        return False

    if constraints.regions:
        allowed: set[str] = set()
        for region in constraints.regions:
            allowed.update(REGION_SOURCE_MAP.get(region, []))
        if allowed and product.source.value not in allowed:
            return False

    if constraints.excluded_conditions:
        if product.condition.value in constraints.excluded_conditions:
            return False

    return True
