#!/usr/bin/env python3
"""Encode catalogue product images into pgvector embeddings.

Production entrypoint for embeddings.indexer.CatalogueIndexer, which until now
was only reachable from unit tests — leaving product_embeddings empty and the
vector retriever with nothing to search.

Usage:
    python scripts/run_indexer.py                # products needing a reindex
    python scripts/run_indexer.py --limit 20     # first 20 of them
    python scripts/run_indexer.py --all          # re-encode the whole catalogue
    python scripts/run_indexer.py --dry-run      # list, encode nothing
    python scripts/run_indexer.py --workers 16   # more parallel downloads

Loading FashionSigLIP takes ~60 s, then each product costs ~236 ms of CPU to
encode and ~520 ms of network to fetch its image. Those overlap: --workers
keeps downloads in flight while the encoder works, which is what separates a
~3 h run over 50 000 products from a ~10 h one. Prefer --limit for a smoke test.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import psycopg2  # noqa: E402

from contracts.product import ProductCondition, ProductRecord, ProductSource  # noqa: E402
from embeddings.indexer import index_batch  # noqa: E402

_LOG = logging.getLogger("swipewear.scripts.run_indexer")

# Columns that exist in the products table (see backend/migrations/).
_COLUMNS = [
    "id", "source", "source_record_id", "title", "brand",
    "price", "condition", "size_raw", "size_eu",
    "category", "image_urls", "available", "embedding_version",
]

_SELECT = """\
SELECT {columns}
FROM products
WHERE image_urls IS NOT NULL
  AND array_length(image_urls, 1) >= 1
  {needs_reindex}
ORDER BY created_at DESC
{limit}"""


def _db_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("ERROR: DATABASE_URL is not set.", file=sys.stderr)
        sys.exit(1)
    return url


def _load_products(conn, *, reindex_all: bool, limit: int | None) -> list[ProductRecord]:
    query = _SELECT.format(
        columns=", ".join(_COLUMNS),
        needs_reindex="" if reindex_all else "AND needs_reindex = TRUE",
        limit=f"LIMIT {int(limit)}" if limit else "",
    )
    with conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()

    records: list[ProductRecord] = []
    for row in rows:
        data = dict(zip(_COLUMNS, row))
        data["source"] = ProductSource(data["source"])
        data["condition"] = ProductCondition(data["condition"])
        data["price"] = float(data["price"])
        data["image_urls"] = list(data["image_urls"] or [])
        records.append(ProductRecord(**data))
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None, help="cap the number of products")
    parser.add_argument("--all", action="store_true", help="re-encode even up-to-date products")
    parser.add_argument("--dry-run", action="store_true", help="list products, encode nothing")
    parser.add_argument(
        "--workers", type=int, default=8,
        help="parallel image downloads (default 8; 1 disables prefetching)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s",
    )

    conn = psycopg2.connect(_db_url())
    try:
        records = _load_products(conn, reindex_all=args.all, limit=args.limit)
    finally:
        conn.close()

    if not records:
        print("Nothing to index — every product already carries a current embedding.")
        return 0

    print(f"{len(records)} product(s) to index.")
    if args.dry_run:
        for record in records:
            print(f"  {record.id}  {record.title[:60]}")
        print("Dry run — no embedding computed.")
        return 0

    result = index_batch(records, max_workers=args.workers)
    print(
        f"Done: attempted={result.attempted} indexed={result.indexed} "
        f"failed={result.failed} marked_for_reindex={result.marked_for_reindex}"
    )
    for product_id, reason in result.failures.items():
        print(f"  FAILED {product_id}: {reason}", file=sys.stderr)

    return 1 if result.indexed == 0 else 0


if __name__ == "__main__":
    sys.exit(main())
