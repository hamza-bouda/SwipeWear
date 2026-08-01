#!/usr/bin/env python3
"""Cron script: send daily drop push notification at 19h (F15).

Invoke via Railway Cron at 19:00 UTC (or local TZ adjusted):
    python scripts/run_drop_notification.py

Sends a push to every user who has a registered device token.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging  # noqa: E402
import os  # noqa: E402

import psycopg2  # noqa: E402

from notifications.push_sender import PushMessage, send_batch  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
_LOG = logging.getLogger("drop.notification")


def main() -> None:
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql://swipewear:swipewear_dev@localhost:5432/swipewear",
    )
    conn = psycopg2.connect(url)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT expo_token FROM device_tokens"
            )
            tokens = [row[0] for row in cur.fetchall()]

        if not tokens:
            _LOG.info("No device tokens registered, skipping drop notification.")
            return

        messages = [
            PushMessage(
                to=token,
                title="Le Drop du jour est arrivé",
                body="15 pépites sélectionnées par ton IA t'attendent. Elles ne dureront pas.",
                data={"type": "drop", "screen": "Drop"},
            )
            for token in tokens
        ]

        batch_size = 100
        total_sent = 0
        for i in range(0, len(messages), batch_size):
            batch = messages[i : i + batch_size]
            receipts = send_batch(batch)
            ok = sum(1 for r in receipts if r.status == "ok")
            total_sent += ok
            _LOG.info("Batch %d: %d/%d sent", i // batch_size + 1, ok, len(batch))

        _LOG.info("Drop notification sent to %d/%d devices.", total_sent, len(tokens))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
