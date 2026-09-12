#!/usr/bin/env python3
"""Watch approved catalogue APIs for active SwipeWear alerts.

This is the production-safe alternative to the isolated Vinted prototype. It
only calls official APIs configured by the deployment (eBay Browse, Etsy Open
API and/or Awin Product Data), stores public product fields, and leaves the
existing alert matcher to enforce size, price and condition constraints.

Usage:
    python scripts/watch_official_sources.py --once

The process is intentionally one-shot so ``run_service.py`` can supervise it
without overlapping runs. No Vinted endpoint is contacted by this module.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

import psycopg2
from psycopg2.extras import Json, execute_values

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.normalizer import NormalizationError, normalize  # noqa: E402
from ingestion.sources.awin import AwinSource  # noqa: E402
from ingestion.sources.ebay import EbaySource  # noqa: E402
from ingestion.sources.etsy import EtsySource  # noqa: E402

_LOG = logging.getLogger("swipewear.official_watcher")
_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
_MAX_RESULTS = 20

_INSERT_SQL = """
INSERT INTO products (
    id, source, source_record_id, title, price, currency, condition,
    size_raw, size_eu, category, image_urls, affiliate_url, available,
    enriched_attrs, schema_version, embedding_version, brand, model, gender,
    listing_url
) VALUES %s
ON CONFLICT (id) DO UPDATE SET
    price         = EXCLUDED.price,
    condition     = EXCLUDED.condition,
    size_raw      = EXCLUDED.size_raw,
    size_eu        = EXCLUDED.size_eu,
    image_urls    = EXCLUDED.image_urls,
    affiliate_url = EXCLUDED.affiliate_url,
    listing_url   = EXCLUDED.listing_url,
    available     = EXCLUDED.available,
    brand         = COALESCE(EXCLUDED.brand, products.brand),
    model         = COALESCE(EXCLUDED.model, products.model),
    gender        = COALESCE(EXCLUDED.gender, products.gender)
"""


def _load_env() -> None:
    if not _ENV_PATH.exists():
        return
    for line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def _active_alert_queries(conn: Any) -> list[tuple[str, dict[str, Any]]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT label, constraints
            FROM alerts
            WHERE status = 'active' AND label IS NOT NULL AND label <> ''
            """
        )
        rows = cur.fetchall()

    queries: list[tuple[str, dict[str, Any]]] = []
    for label, constraints in rows:
        if isinstance(constraints, dict):
            parsed = constraints
        else:
            try:
                parsed = json.loads(constraints or "{}")
            except (TypeError, json.JSONDecodeError):
                parsed = {}
        filters: dict[str, Any] = {"limit": _MAX_RESULTS}
        if parsed.get("max_price_eur") is not None:
            filters["max_price"] = parsed["max_price_eur"]
        queries.append((str(label), filters))
    return queries


def _build_sources(names: list[str]) -> dict[str, Any]:
    sources: dict[str, Any] = {}
    for name in names:
        normalized = name.strip().lower()
        if normalized == "vinted":
            raise ValueError(
                "Vinted is isolated and disabled pending legal review; "
                "use an approved official source instead."
            )
        try:
            if normalized == "ebay":
                sources[normalized] = EbaySource()
            elif normalized == "etsy":
                sources[normalized] = EtsySource()
            elif normalized == "awin":
                sources[normalized] = AwinSource()
            elif normalized:
                _LOG.warning("Unknown official watcher source %r — skipped", name)
        except KeyError as exc:
            _LOG.warning(
                "Official source %s skipped: missing environment variable %s",
                normalized,
                exc.args[0],
            )
    return sources


def _row(record: Any) -> tuple[Any, ...]:
    return (
        record.id,
        record.source.value,
        record.source_record_id,
        record.title,
        record.price,
        record.currency,
        record.condition.value,
        record.size_raw,
        record.size_eu,
        record.category,
        list(record.image_urls),
        record.affiliate_url,
        record.available,
        Json(record.enriched_attrs),
        record.schema_version,
        record.embedding_version,
        record.brand,
        record.model,
        record.gender.value if record.gender else None,
        record.affiliate_url,
    )


def run_once(conn: Any, source_names: list[str]) -> int:
    sources = _build_sources(source_names)
    if not sources:
        _LOG.warning("No official watcher source is configured")
        return 0

    queries = _active_alert_queries(conn)
    if not queries:
        _LOG.info("No active alert queries — nothing to watch")
        return 0

    rows: list[tuple[Any, ...]] = []
    fetched = 0
    for source_name, source in sources.items():
        for query, filters in queries:
            try:
                raw_items = source.fetch(query, filters)
            except Exception:
                _LOG.warning("%s fetch failed for %r", source_name, query, exc_info=True)
                continue
            fetched += len(raw_items)
            for raw in raw_items:
                try:
                    rows.append(_row(normalize(source_name, raw)))
                except NormalizationError as exc:
                    _LOG.debug("Skipping %s result: %s", source_name, exc)

    if not rows:
        _LOG.info("Official watcher fetched %d item(s), no valid rows", fetched)
        return 0

    with conn.cursor() as cur:
        execute_values(cur, _INSERT_SQL, rows, page_size=500)
    conn.commit()
    _LOG.info(
        "Official watcher complete: sources=%s queries=%d fetched=%d upserted=%d",
        ",".join(sources),
        len(queries),
        fetched,
        len(rows),
    )
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sources",
        default=os.getenv("OFFICIAL_WATCHER_SOURCES", "ebay"),
        help="Comma-separated official sources: ebay, etsy, awin",
    )
    parser.add_argument("--once", action="store_true", help="Run one pass and exit")
    args = parser.parse_args()
    _load_env()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        _LOG.error("DATABASE_URL is not set")
        return 1
    try:
        source_names = [item for item in args.sources.split(",") if item.strip()]
        conn = psycopg2.connect(database_url)
        try:
            run_once(conn, source_names)
        finally:
            conn.close()
    except ValueError as exc:
        _LOG.error("%s", exc)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
