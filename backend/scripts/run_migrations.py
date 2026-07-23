#!/usr/bin/env python3
"""Apply all SQL migrations in order before starting the server.

Migrations are applied in filename order (001_, 002_, …).
Each migration is run inside a transaction; any SQL error aborts the
startup so Railway marks the deploy as failed rather than starting a
broken server.

Idempotency: every migration uses CREATE TABLE IF NOT EXISTS, ALTER …
ADD COLUMN IF NOT EXISTS, CREATE INDEX IF NOT EXISTS, or explicit
ON CONFLICT DO NOTHING — so re-running is safe.

Usage (run automatically by Dockerfile CMD before uvicorn):
    python scripts/run_migrations.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg2

_MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def _db_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("ERROR: DATABASE_URL is not set.", file=sys.stderr)
        sys.exit(1)
    return url


def run() -> None:
    url = _db_url()
    migrations = sorted(_MIGRATIONS_DIR.glob("*.sql"))
    if not migrations:
        print("No SQL migrations found — nothing to apply.")
        return

    print(f"Applying {len(migrations)} migration(s) from {_MIGRATIONS_DIR} …")
    conn = psycopg2.connect(url)
    try:
        conn.autocommit = False
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS _migrations (
                    filename TEXT PRIMARY KEY,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            conn.commit()

        for migration in migrations:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM _migrations WHERE filename = %s",
                    (migration.name,),
                )
                if cur.fetchone():
                    print(f"  SKIP  {migration.name} (already applied)")
                    continue

            sql = migration.read_text(encoding="utf-8")
            try:
                with conn.cursor() as cur:
                    cur.execute(sql)
                    cur.execute(
                        "INSERT INTO _migrations (filename) VALUES (%s)",
                        (migration.name,),
                    )
                conn.commit()
                print(f"  OK    {migration.name}")
            except Exception as exc:
                conn.rollback()
                print(f"  FAIL  {migration.name}: {exc}", file=sys.stderr)
                sys.exit(1)
    finally:
        conn.close()

    print("All migrations applied successfully.")


if __name__ == "__main__":
    run()
