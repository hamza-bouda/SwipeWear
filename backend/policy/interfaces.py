"""Policy module public interface.

Other modules import from here -- never from internal files (blueprint SS11).
"""
from __future__ import annotations

from policy.diversity import mmr_rerank  # noqa: F401
