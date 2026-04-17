#!/usr/bin/env python3
"""Ingest real products from eBay Browse API into the products table.

Usage:
    python backend/scripts/ingest_ebay.py
    python backend/scripts/ingest_ebay.py --queries "nike sneakers" "levi's jeans"
    python backend/scripts/ingest_ebay.py --limit 30 --reset

Reads EBAY_CLIENT_ID, EBAY_CLIENT_SECRET, EBAY_ENV, DATABASE_URL from .env.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

import psycopg2

# ── Load .env from project root ─────────────────────────────────────────────
_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
if _ENV_PATH.exists():
    for line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

# Add backend to path so imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.sources.ebay import EbaySource  # noqa: E402
from ingestion.normalizer import normalize, NormalizationError  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("ingest_ebay")

DEFAULT_QUERIES = [
    "nike sneakers occasion",
    "adidas sneakers vintage",
    "new balance 574",
    "veste the north face occasion",
    "veste carhartt",
    "levi's 501 jeans",
    "jean slim homme occasion",
    "t-shirt champion vintage",
    "polo lacoste occasion",
    "sac the north face",
    "casquette nike",
    "dr martens boots occasion",
    "veste patagonia fleece",
    "converse chuck taylor",
    "puma suede classic",
]

_INSERT_SQL = """
INSERT INTO products
    (id, source, source_record_id, title, price, condition,
     category, image_urls, size_raw, size_eu, brand)
VALUES
    (%(id)s, %(source)s, %(source_record_id)s, %(title)s,
     %(price)s, %(condition)s, %(category)s, %(image_urls)s,
     %(size_raw)s, %(size_eu)s, %(brand)s)
ON CONFLICT (id) DO UPDATE SET
    price = EXCLUDED.price,
    condition = EXCLUDED.condition,
    image_urls = EXCLUDED.image_urls,
    title = EXCLUDED.title
"""


def ingest(queries: list[str], limit: int, reset: bool) -> None:
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        log.error("DATABASE_URL not set. Check your .env file.")
        sys.exit(1)

    source = EbaySource()
    conn = psycopg2.connect(db_url)

    try:
        if reset:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM products WHERE source = 'ebay'"
                    " AND id LIKE 'ebay-%'"
                )
                log.info("Cleared existing eBay products.")
            conn.commit()

        total_inserted = 0
        total_skipped = 0

        for query in queries:
            log.info("Fetching: %s (limit=%d)", query, limit)
            try:
                raw_items = source.fetch(query, {"limit": limit})
            except Exception as exc:
                log.error("eBay fetch failed for %r: %s", query, exc)
                continue

            for raw in raw_items:
                try:
                    record = normalize("ebay", raw)
                except NormalizationError as exc:
                    log.warning("Skip: %s", exc)
                    total_skipped += 1
                    continue

                with conn.cursor() as cur:
                    cur.execute(_INSERT_SQL, {
                        "id": record.id,
                        "source": record.source.value,
                        "source_record_id": record.source_record_id,
                        "title": record.title,
                        "price": record.price,
                        "condition": record.condition.value,
                        "category": record.category,
                        "image_urls": list(record.image_urls),
                        "size_raw": record.size_raw,
                        "size_eu": record.size_eu,
                        "brand": record.brand,
                    })
                    total_inserted += 1

            conn.commit()
            log.info(
                "  → %d items from %r", len(raw_items), query
            )

        log.info(
            "Done! %d products inserted/updated, %d skipped.",
            total_inserted, total_skipped,
        )

        with conn.cursor() as cur:
            cur.execute(
                "SELECT category, COUNT(*) FROM products"
                " WHERE source = 'ebay'"
                " GROUP BY category ORDER BY category"
            )
            log.info("eBay products by category:")
            for cat, cnt in cur.fetchall():
                log.info("  %s: %d", cat, cnt)
            cur.execute(
                "SELECT COUNT(*) FROM products WHERE source = 'ebay'"
            )
            total = cur.fetchone()[0]
            log.info("  TOTAL: %d", total)

    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest eBay products")
    parser.add_argument(
        "--queries", nargs="+", default=DEFAULT_QUERIES,
        help="Search queries to run",
    )
    parser.add_argument(
        "--limit", type=int, default=20,
        help="Max results per query (default 20)",
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Delete existing eBay products before ingesting",
    )
    args = parser.parse_args()
    ingest(args.queries, args.limit, args.reset)


if __name__ == "__main__":
    main()
