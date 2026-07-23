#!/usr/bin/env python3
"""Rebuild every user's profile from the event log (KAN-35).

Usage:
    cd backend
    python scripts/rebuild_all_profiles.py
    python scripts/rebuild_all_profiles.py --until 2026-07-01T00:00:00+00:00

Reads DATABASE_URL from .env (via dotenv) or environment. One user's
failure is logged and skipped rather than aborting the whole run -- a
single corrupt event must not block rebuilding everyone else.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from preferences.rebuild import rebuild_profile  # noqa: E402
from preferences.store import ProfileStore  # noqa: E402

# ── Load .env from project root ──────────────────────────────────────────────
_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
if _ENV_PATH.exists():
    for line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())


def _distinct_user_ids(conn) -> list[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT user_id FROM interaction_events")
        return [str(row[0]) for row in cur.fetchall()]


def rebuild_all(conn, until: datetime | None) -> tuple[int, list[tuple[str, Exception]]]:
    store = ProfileStore(get_conn=lambda: conn)
    user_ids = _distinct_user_ids(conn)
    total = len(user_ids)
    rebuilt = 0
    failures: list[tuple[str, Exception]] = []

    for i, user_id in enumerate(user_ids, start=1):
        print(f"\r[{i}/{total}] rebuilding {user_id}...", end="", flush=True)
        try:
            profile = rebuild_profile(user_id, until, get_conn=lambda: conn)
            store.save(profile)
            rebuilt += 1
        except Exception as exc:  # noqa: BLE001 - one bad user must not abort the batch
            failures.append((user_id, exc))

    print()
    return rebuilt, failures


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild all profiles from the event log")
    parser.add_argument(
        "--until",
        type=datetime.fromisoformat,
        default=None,
        help="ISO timestamp bound (e.g. 2026-07-01T00:00:00+00:00); omit for full replay",
    )
    args = parser.parse_args()

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL not set. Check your .env file.")
        sys.exit(1)

    conn = psycopg2.connect(db_url)
    try:
        rebuilt, failures = rebuild_all(conn, args.until)
        print(f"Done! {rebuilt} profile(s) rebuilt, {len(failures)} failed.")
        for user_id, exc in failures:
            print(f"  FAILED {user_id}: {type(exc).__name__}: {exc}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
