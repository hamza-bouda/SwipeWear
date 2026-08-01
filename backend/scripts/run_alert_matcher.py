#!/usr/bin/env python3
"""Cron script: batch alert matching (F11).

Invoke every hour via Railway Cron or system cron:
    python scripts/run_alert_matcher.py [--window-hours 2]

Scans products added within the last N hours against all active alerts
using FashionSigLIP embeddings (pgvector). The default 2-hour window
with a 1-hour cron ensures overlap so no product is missed.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging  # noqa: E402
import os  # noqa: E402

import psycopg2  # noqa: E402

from alerts.matcher import run_batch_matching  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
_LOG = logging.getLogger("alerts.matcher.cron")


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch alert matcher")
    parser.add_argument(
        "--window-hours", type=int, default=2,
        help="Scan products added in the last N hours (default: 2)",
    )
    args = parser.parse_args()

    url = os.environ.get(
        "DATABASE_URL",
        "postgresql://swipewear:swipewear_dev@localhost:5432/swipewear",
    )
    conn = psycopg2.connect(url)
    try:
        enqueued = run_batch_matching(conn, window_hours=args.window_hours)
        _LOG.info("Done. %d notification(s) enqueued.", enqueued)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
