"""Admin endpoints for watcher kill-switch (KAN-72).

POST /admin/watcher/{source}/enable   — re-enable a watcher source
POST /admin/watcher/{source}/disable  — disable a watcher source (kill switch)
GET  /admin/watcher                   — list all watcher sources and their status

These endpoints are intentionally unprotected at the auth layer in dev;
add admin-role middleware before production exposure.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.db import get_conn, put_conn

router = APIRouter(prefix="/admin/watcher", tags=["watcher-admin"])


def _set_enabled(source: str, enabled: bool) -> dict:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO watcher_sources (source, enabled, updated_at)
                VALUES (%s, %s, now())
                ON CONFLICT (source) DO UPDATE
                    SET enabled = EXCLUDED.enabled,
                        updated_at = now()
                """,
                (source, enabled),
            )
        conn.commit()
    finally:
        put_conn(conn)
    return {"source": source, "enabled": enabled}


@router.get("", summary="List watcher sources")
def list_watcher_sources() -> list[dict]:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT source, enabled, updated_at FROM watcher_sources ORDER BY source")
            rows = cur.fetchall()
    finally:
        put_conn(conn)
    return [{"source": r[0], "enabled": r[1], "updated_at": str(r[2])} for r in rows]


@router.post("/{source}/enable", summary="Enable a watcher source")
def enable_watcher(source: str) -> dict:
    return _set_enabled(source, True)


@router.post("/{source}/disable", summary="Disable a watcher source (kill switch)")
def disable_watcher(source: str) -> dict:
    return _set_enabled(source, False)
