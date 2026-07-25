#!/usr/bin/env python3
"""Bulk-ingest the eBay catalogue into the products table.

scripts/ingest_ebay.py inserts one row per round-trip and has no paging, so it
tops out at 200 items per query and takes hours for a catalogue worth having.
This script pages, batches, and resumes.

Usage:
    python scripts/ingest_catalogue.py --target 50000
    python scripts/ingest_catalogue.py --target 5000 --resume
    python scripts/ingest_catalogue.py --dry-run          # fetch, insert nothing

Reads EBAY_CLIENT_ID, EBAY_CLIENT_SECRET, EBAY_ENV, DATABASE_URL from .env.

Two eBay limits shape the design: a single query can never yield more than
10 000 items (offset cap), so breadth comes from many queries; and the app is
capped at ~5 000 calls/day, so at 200 items/call the practical daily ceiling is
around 1M gross fetches — paging is never the bottleneck, duplicate overlap is.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from itertools import zip_longest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import psycopg2  # noqa: E402
from psycopg2.extras import execute_values  # noqa: E402

from ingestion.normalizer import NormalizationError, normalize  # noqa: E402
from ingestion.sources.ebay import MAX_LIMIT, MAX_OFFSET, EbaySource  # noqa: E402

_LOG = logging.getLogger("swipewear.scripts.ingest_catalogue")

_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
_STATE_PATH = Path(__file__).resolve().parent.parent / ".ingest_state.json"

_PAGE_SIZE = MAX_LIMIT
_FLUSH_EVERY = 500
# eBay tolerates far more, but a short pause keeps a long run well clear of
# the burst thresholds that trigger 429s.
_PAUSE_S = 0.15

# Query plan — brands crossed with each of the five internal categories.
# Breadth matters more than depth: every query shares the same 10 000-item
# ceiling, so more queries is the only way to grow the catalogue.
_BRANDS: dict[str, list[str]] = {
    "sneakers": [
        "nike", "adidas", "new balance", "puma", "converse", "vans",
        "asics", "reebok", "jordan", "veja", "dr martens", "timberland",
        "salomon", "lacoste", "fila",
    ],
    "vestes": [
        "the north face", "carhartt", "patagonia", "levi's", "schott",
        "barbour", "columbia", "napapijri", "helly hansen", "jack wolfskin",
        "uniqlo", "adidas", "nike", "stone island",
    ],
    "jeans": [
        "levi's", "wrangler", "lee", "diesel", "carhartt", "dickies",
        "g-star", "pepe jeans", "tommy hilfiger", "calvin klein",
    ],
    "tee-shirts": [
        "champion", "ralph lauren", "lacoste", "stone island", "nike",
        "adidas", "carhartt", "tommy hilfiger", "fred perry", "kappa",
        "sergio tacchini", "umbro",
    ],
    "accessoires": [
        "eastpak", "herschel", "the north face", "nike", "carhartt",
        "ray-ban", "casio", "longchamp", "michael kors", "fjallraven",
    ],
}

# French search nouns per category — the marketplace is EBAY_FR.
_NOUNS: dict[str, list[str]] = {
    "sneakers": ["sneakers", "baskets", "chaussures"],
    "vestes": ["veste", "manteau", "blouson"],
    "jeans": ["jean", "pantalon"],
    "tee-shirts": ["t-shirt", "sweat", "polo"],
    "accessoires": ["sac", "casquette", "ceinture"],
}

_INSERT_SQL = """
INSERT INTO products
    (id, source, source_record_id, title, price, condition, category,
     image_urls, size_raw, size_eu, brand, model, listing_url, available)
VALUES %s
ON CONFLICT (id) DO UPDATE SET
    price       = EXCLUDED.price,
    condition   = EXCLUDED.condition,
    image_urls  = EXCLUDED.image_urls,
    title       = EXCLUDED.title,
    listing_url = EXCLUDED.listing_url,
    -- COALESCE, not assignment: the same item surfaces under several queries
    -- and only some of them can attribute a brand. A plain EXCLUDED.brand
    -- would let a later NULL erase a value an earlier query resolved.
    brand       = COALESCE(EXCLUDED.brand, products.brand),
    model       = COALESCE(EXCLUDED.model, products.model)
"""


def _load_env() -> None:
    if not _ENV_PATH.exists():
        return
    for line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip())


def build_query_plan() -> list[tuple[str, str]]:
    """Return (brand, query) pairs, interleaved across categories.

    Round-robin rather than category-major: the run stops the moment --target
    is hit, so a grouped plan would spend the entire budget on sneakers and
    leave accessoires with a handful of items. Interleaving keeps the five
    categories proportionate whenever the run ends early.
    """
    per_category: list[list[tuple[str, str]]] = []
    for category, brands in _BRANDS.items():
        queries = [
            (brand, f"{brand} {noun}")
            for noun in _NOUNS[category]
            for brand in brands
        ]
        per_category.append(queries)

    plan: list[tuple[str, str]] = []
    seen: set[str] = set()
    for row in zip_longest(*per_category):
        for pair in row:
            if pair is not None and pair[1] not in seen:
                seen.add(pair[1])
                plan.append(pair)
    return plan


def _attribute_brand(raw: dict, brand: str) -> dict:
    """Fill in the brand eBay omits, but only when the title agrees.

    itemSummary carries no brand field, which would leave every row NULL —
    breaking the deduplicator's (brand, model) fingerprint and pinning the
    price ladder to 'similar' forever. The search term is a strong hint, yet
    'nike sneakers' also returns Adidas: attributing blind would mislabel
    stock, so the title has to confirm it.
    """
    if raw.get("brand"):
        return raw
    if brand.lower() in (raw.get("title") or "").lower():
        raw["brand"] = brand
    return raw


def _load_state(resume: bool) -> set[str]:
    """Return the set of already-fetched 'query@offset' keys."""
    if not resume or not _STATE_PATH.exists():
        return set()
    try:
        return set(json.loads(_STATE_PATH.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError):
        _LOG.warning("Ignoring unreadable state file %s", _STATE_PATH)
        return set()


def _save_state(done: set[str]) -> None:
    _STATE_PATH.write_text(json.dumps(sorted(done)), encoding="utf-8")


def _to_row(record) -> tuple:
    return (
        record.id,
        record.source.value,
        record.source_record_id,
        record.title,
        record.price,
        record.condition.value,
        record.category,
        list(record.image_urls),
        record.size_raw,
        record.size_eu,
        record.brand,
        record.model,
        # normalize() parks the seller URL on the contract's affiliate_url;
        # the column stores it raw so affiliate links stay a serve-time concern.
        record.affiliate_url,
        True,
    )


def _flush(conn, rows: list[tuple], dry_run: bool) -> int:
    if not rows or dry_run:
        return 0
    with conn.cursor() as cur:
        execute_values(cur, _INSERT_SQL, rows, page_size=len(rows))
    conn.commit()
    return len(rows)


def _count_products(conn) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM products WHERE source = 'ebay'")
        return int(cur.fetchone()[0])


def ingest(target: int, resume: bool, dry_run: bool) -> int:
    source = EbaySource()
    queries = build_query_plan()
    done = _load_state(resume)
    max_pages = MAX_OFFSET // _PAGE_SIZE

    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    try:
        start_count = _count_products(conn)
        _LOG.info(
            "%d queries planned, %d products already stored, target %d",
            len(queries), start_count, target,
        )

        pending: list[tuple] = []
        fetched = written = skipped = 0
        exhausted: set[str] = set()
        # Refreshed after each flush rather than polled per query: COUNT(*) on
        # a growing table, once per query, would cost more than the fetches.
        stored = 0

        # Page-major: sweep every query at offset 0, then at 200, and so on.
        # Depth-first would spend the whole budget on the first few queries and
        # leave the catalogue lopsided if the run is interrupted.
        for page in range(max_pages):
            offset = page * _PAGE_SIZE
            if offset + _PAGE_SIZE > MAX_OFFSET:
                break
            for brand, query in queries:
                if stored + len(pending) >= target:
                    break
                if query in exhausted:
                    continue
                key = f"{query}@{offset}"
                if key in done:
                    continue

                try:
                    raw_items = source.fetch(
                        query, {"limit": _PAGE_SIZE, "offset": offset}
                    )
                except Exception as exc:  # noqa: BLE001 - one bad query must not end the run
                    _LOG.warning("fetch failed for %r@%d: %s", query, offset, exc)
                    continue

                done.add(key)
                if not raw_items:
                    exhausted.add(query)
                    continue

                fetched += len(raw_items)
                for raw in raw_items:
                    try:
                        record = normalize("ebay", _attribute_brand(raw, brand))
                    except NormalizationError:
                        skipped += 1
                        continue
                    pending.append(_to_row(record))

                if len(pending) >= _FLUSH_EVERY:
                    written += _flush(conn, pending, dry_run)
                    pending.clear()
                    _save_state(done)
                    stored = _count_products(conn) - start_count
                    _LOG.info(
                        "page %d | fetched=%d written=%d skipped=%d | new in DB=%d",
                        page, fetched, written, skipped, stored,
                    )
                time.sleep(_PAUSE_S)

            if stored + len(pending) >= target:
                _LOG.info("Target reached at page %d.", page)
                break
            if len(exhausted) == len(queries):
                _LOG.info("Every query exhausted at page %d.", page)
                break

        written += _flush(conn, pending, dry_run)
        _save_state(done)

        end_count = _count_products(conn)
        _LOG.info(
            "Done: fetched=%d rows_written=%d skipped=%d | ebay products %d -> %d",
            fetched, written, skipped, start_count, end_count,
        )
        _report(conn)
        return 0
    finally:
        conn.close()


def _report(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT category, COUNT(*), ROUND(AVG(price)::numeric, 2)"
            " FROM products WHERE source = 'ebay'"
            " GROUP BY category ORDER BY COUNT(*) DESC"
        )
        _LOG.info("eBay catalogue by category:")
        for cat, cnt, avg in cur.fetchall():
            _LOG.info("  %-12s %6d  avg %s EUR", cat, cnt, avg)
        cur.execute(
            "SELECT COUNT(*) FROM products"
            " WHERE source = 'ebay' AND listing_url IS NOT NULL"
        )
        _LOG.info("  with listing_url: %d", cur.fetchone()[0])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=int, default=50_000,
                        help="stop once this many new products are stored")
    parser.add_argument("--resume", action="store_true",
                        help="skip query/offset pairs already fetched")
    parser.add_argument("--dry-run", action="store_true",
                        help="fetch and normalise but write nothing")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s",
    )
    _load_env()
    if not os.environ.get("DATABASE_URL"):
        print("ERROR: DATABASE_URL is not set.", file=sys.stderr)
        return 1
    return ingest(args.target, args.resume, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
