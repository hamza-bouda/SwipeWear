"""Configuration for the Vinted watcher process (KAN-72).

All settings come from environment variables. The watcher reads these at
startup; changing them requires restarting the watcher process only — the
backend API is not affected.

IMPORTANT: Do not import this module from backend/. The watcher is intentionally
isolated. Any coupling via imports defeats the "survive without" architecture.
"""
from __future__ import annotations

import os

# -- Database (shared with backend, read-only from watcher's perspective) ------
DATABASE_URL: str = os.environ.get(
    "DATABASE_URL",
    "postgresql://swipewear:swipewear_dev@localhost:5432/swipewear",
)

# -- Kill switch ---------------------------------------------------------------
# The authoritative kill switch is the watcher_sources DB table (checked via
# the backend admin endpoint). This env flag is an additional local guard:
# if VINTED_ENABLED is not "true", the process exits immediately at startup
# before opening any network connection to Vinted.
VINTED_ENABLED: bool = os.environ.get("VINTED_ENABLED", "false").lower() == "true"

# -- Cadence -------------------------------------------------------------------
# Seconds between successive watcher runs. Keep generous to avoid rate-limiting.
# Targeted at active alerts only — never a full-catalogue crawl.
WATCHER_CADENCE_SECONDS: int = int(os.environ.get("WATCHER_CADENCE_SECONDS", "300"))

# Maximum listings fetched per alert keyword per run.
MAX_LISTINGS_PER_KEYWORD: int = int(os.environ.get("MAX_LISTINGS_PER_KEYWORD", "20"))

# -- HTTP headers --------------------------------------------------------------
# Identify ourselves honestly; do not spoof a real browser.
USER_AGENT: str = os.environ.get(
    "WATCHER_USER_AGENT",
    "SwipeWear-Watcher/0.1 (research; contact: hamzabouda661@gmail.com)",
)
