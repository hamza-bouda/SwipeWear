"""Retrieval module public interface.

Other modules import from here -- never from internal files (blueprint SS11).
"""
from __future__ import annotations

from retrieval.filters import (  # noqa: F401
    REGION_SOURCE_MAP,
    HardFilterResult,
    apply_hard_filters,
    matches_hard_filters,
)
from retrieval.fallback import (  # noqa: F401
    FallbackRetriever,
    retrieve_with_fallback,
)
from retrieval.retriever import VectorRetriever  # noqa: F401
