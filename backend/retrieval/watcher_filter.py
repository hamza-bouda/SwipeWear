"""Kill-switch helper: reads watcher_sources table to find disabled sources (KAN-72).

Called by VectorRetriever at query time so the feed reflects the current DB state
without a redeploy (< 1 request latency after an UPDATE on watcher_sources).
"""
from __future__ import annotations

from typing import Any


def get_disabled_watcher_sources(conn: Any) -> list[str]:
    """Return list of source names whose watcher is currently disabled."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT source FROM watcher_sources WHERE enabled = false"
        )
        rows = cur.fetchall()
    return [row[0] for row in rows]
