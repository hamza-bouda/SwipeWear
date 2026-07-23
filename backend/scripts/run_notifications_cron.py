#!/usr/bin/env python3
"""Cron script: flush due push notifications (KAN-71).

Invoke every minute via Railway Cron or system cron:
    python scripts/run_notifications_cron.py

Reads DATABASE_URL from environment. Exits 0 on success.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure backend/ is on sys.path when run directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
import os

import psycopg2

from notifications.notification_store import flush_due_notifications

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
_LOG = logging.getLogger("notifications.cron")


def main() -> None:
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql://swipewear:swipewear_dev@localhost:5432/swipewear",
    )
    conn = psycopg2.connect(url)
    try:
        sent = flush_due_notifications(conn)
        _LOG.info("Sent %d push notification(s).", sent)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
