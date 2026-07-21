"""Ranking feature weights — all configurable (blueprint SS11)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RankingWeights:
    similarity: float = 0.50
    price_fit: float = 0.20
    brand_boost: float = 0.15
    freshness: float = 0.15


DEFAULT_WEIGHTS = RankingWeights()

PRICE_FIT_THRESHOLD = 0.80
FRESHNESS_HALF_LIFE_DAYS = 7.0
