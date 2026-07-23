"""Vinted watcher main loop (KAN-72) — SKELETON, NOT PRODUCTION-READY.

╔═══════════════════════════════════════════════════════════════════════╗
║  LEGAL REVIEW REQUIRED BEFORE ACTIVATION                             ║
║  See LEGAL_REVIEW.md for the checklist.                              ║
║  The actual HTTP fetch to Vinted is stubbed (_fetch_listings).       ║
║  Do NOT implement _fetch_listings until legal sign-off is obtained.  ║
╚═══════════════════════════════════════════════════════════════════════╝

Architecture constraints (KAN-72):
- This process NEVER imports from backend/. It writes directly to the DB.
- Communication = one direction only: watcher writes rows to products table.
- The backend read-path filters source='vinted' via the kill switch.
- Kill switch is checked at DB level: if watcher_sources.enabled=false,
  the watcher exits without writing any rows.
"""
from __future__ import annotations

import json
import logging
import sys
import time
from typing import Any

import psycopg2

from watcher.config import (
    DATABASE_URL,
    MAX_LISTINGS_PER_KEYWORD,
    VINTED_ENABLED,
    WATCHER_CADENCE_SECONDS,
)
from watcher.models import VintedListing
from watcher.normalizer import normalise

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
_LOG = logging.getLogger("swipewear.watcher.vinted")

_UPSERT_SQL = """
INSERT INTO products (
    id, source, source_record_id, title, brand, model,
    price, currency, condition, size_raw, size_eu,
    category, image_urls, affiliate_url, available,
    enriched_attrs, schema_version, embedding_version
) VALUES (
    %(id)s, %(source)s, %(source_record_id)s, %(title)s, %(brand)s, %(model)s,
    %(price)s, %(currency)s, %(condition)s, %(size_raw)s, %(size_eu)s,
    %(category)s, %(image_urls)s, %(affiliate_url)s, %(available)s,
    %(enriched_attrs)s, %(schema_version)s, %(embedding_version)s
)
ON CONFLICT (id) DO UPDATE SET
    price         = EXCLUDED.price,
    available     = EXCLUDED.available,
    image_urls    = EXCLUDED.image_urls,
    affiliate_url = EXCLUDED.affiliate_url;
"""


def _is_kill_switch_active(conn: Any) -> bool:
    """Return True if Vinted is disabled in watcher_sources table."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT enabled FROM watcher_sources WHERE source = 'vinted'"
            )
            row = cur.fetchone()
        return row is None or not row[0]
    except Exception:
        _LOG.exception("Could not read watcher_sources — treating as disabled")
        return True


def _fetch_active_alert_keywords(conn: Any) -> list[str]:
    """Return labels from active specific_item alerts to drive targeted search."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT DISTINCT label FROM alerts WHERE status = 'active' AND alert_type = 'specific_item'"
        )
        rows = cur.fetchall()
    return [r[0] for r in rows if r[0]]


def _fetch_listings(keyword: str, max_results: int) -> list[VintedListing]:
    """Fetch Vinted listings for keyword. NOT IMPLEMENTED — legal review required.

    When legal sign-off is obtained, implement this function to call the
    Vinted internal API (or HTML endpoint) and return VintedListing objects.
    Do NOT collect seller personal data (profile ID, location, ratings).

    Returns an empty list until implementation is authorized.
    """
    _LOG.warning(
        "fetch_listings called for %r but Vinted HTTP integration is not "
        "implemented (pending legal review). Returning empty list.",
        keyword,
    )
    return []


def _upsert_listing(conn: Any, listing: VintedListing) -> bool:
    """Normalise and upsert one listing. Returns True if written."""
    try:
        row = normalise(listing)
    except ValueError as exc:
        _LOG.debug("Skipping listing %s: %s", listing.listing_id, exc)
        return False

    row["image_urls"] = json.dumps(row["image_urls"])
    row["enriched_attrs"] = json.dumps(row["enriched_attrs"])

    with conn.cursor() as cur:
        cur.execute(_UPSERT_SQL, row)
    return True


def run_once(conn: Any) -> int:
    """Single watcher pass. Returns count of listings written."""
    if _is_kill_switch_active(conn):
        _LOG.info("Kill switch active for Vinted — skipping run")
        return 0

    keywords = _fetch_active_alert_keywords(conn)
    if not keywords:
        _LOG.info("No active alert keywords — nothing to watch")
        return 0

    _LOG.info("Running Vinted watcher for %d keyword(s)", len(keywords))
    written = 0
    for keyword in keywords:
        listings = _fetch_listings(keyword, MAX_LISTINGS_PER_KEYWORD)
        for listing in listings:
            if _upsert_listing(conn, listing):
                written += 1
        conn.commit()

    _LOG.info("Watcher run complete: %d listing(s) written", written)
    return written


def main() -> None:
    if not VINTED_ENABLED:
        _LOG.warning(
            "VINTED_ENABLED is not 'true' — watcher will not run. "
            "Set VINTED_ENABLED=true after legal review to activate."
        )
        sys.exit(0)

    _LOG.info("Vinted watcher starting (cadence=%ds)", WATCHER_CADENCE_SECONDS)
    conn = psycopg2.connect(DATABASE_URL)
    try:
        while True:
            try:
                run_once(conn)
            except Exception:
                _LOG.exception("Watcher run failed — will retry next cycle")
                conn.rollback()
            time.sleep(WATCHER_CADENCE_SECONDS)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
