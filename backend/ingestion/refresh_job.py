"""Periodic refresh job: deduplication + stale product cleanup.

Usage:
    store = MyPostgresStore(...)
    result = run_refresh(store, fresh_records)

The job is designed to be called by a scheduler (cron, APScheduler, etc.)
every time a batch of fresh records arrives from the connectors.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol

from contracts.product import ProductRecord
from ingestion.deduplicator import deduplicate

_LOG = logging.getLogger("swipewear.ingestion.refresh")

_STALE_AFTER = timedelta(hours=24)
_REMOVE_AFTER = timedelta(days=7)


# ── Store contract ────────────────────────────────────────────────────────────

class CatalogueStore(Protocol):
    """Minimal storage interface required by the refresh job.

    Implementations connect to Postgres + pgvector (KAN-22).
    Tests inject a mock — no real DB needed.
    """

    def upsert_all(self, records: list[ProductRecord]) -> None:
        """Persist or update all records (price, availability)."""
        ...

    def mark_unavailable(self, product_id: str) -> None:
        """Set available=False and record the timestamp."""
        ...

    def get_unavailable_since(self, since: datetime) -> list[ProductRecord]:
        """Return products that became unavailable before `since`."""
        ...

    def remove_from_index(self, product_id: str) -> None:
        """Delete the product's embedding row from product_embeddings."""
        ...


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class JobResult:
    updated: int = 0
    deduplicated: int = 0
    removed: int = 0


# ── Job ───────────────────────────────────────────────────────────────────────

def run_refresh(
    store: CatalogueStore,
    fresh_records: list[ProductRecord],
    *,
    now: datetime | None = None,
) -> JobResult:
    """Refresh the catalogue with a new batch of records.

    Steps:
    1. Deduplicate fresh_records across sources.
    2. Persist all records; mark duplicates unavailable.
    3. Remove from vector index products unavailable for > 7 days.
    4. Log updated / deduplicated / removed counts.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    result = JobResult()

    # ── Step 1 & 2: deduplication + persist ──────────────────────────────────
    deduped = deduplicate(fresh_records)
    available = [r for r in deduped if r.available]
    duplicates = [r for r in deduped if not r.available]

    store.upsert_all(deduped)
    result.updated = len(available)
    result.deduplicated = len(duplicates)

    for dup in duplicates:
        store.mark_unavailable(dup.id)

    # ── Step 3: prune long-unavailable products from vector index ─────────────
    cutoff = now - _REMOVE_AFTER
    to_remove = store.get_unavailable_since(cutoff)
    for rec in to_remove:
        store.remove_from_index(rec.id)
    result.removed = len(to_remove)

    # ── Step 4: log summary ───────────────────────────────────────────────────
    _LOG.info(
        "Refresh job complete — updated=%d deduplicated=%d removed=%d",
        result.updated,
        result.deduplicated,
        result.removed,
        extra={
            "pipe_module": "ingestion.refresh",
            "updated": result.updated,
            "deduplicated": result.deduplicated,
            "removed": result.removed,
        },
    )
    return result
