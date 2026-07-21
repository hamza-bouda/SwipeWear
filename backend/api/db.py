"""Database connection pool for FastAPI — shared across all endpoints."""
from __future__ import annotations

import logging
import os
from typing import Any

from psycopg2 import pool

_LOG = logging.getLogger("swipewear.api.db")

_pool: pool.SimpleConnectionPool | None = None


def _get_database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql://swipewear:swipewear_dev@localhost:5432/swipewear",
    )


def init_pool(minconn: int = 1, maxconn: int = 10) -> None:
    global _pool
    if _pool is not None:
        return
    _pool = pool.SimpleConnectionPool(minconn, maxconn, _get_database_url())
    _LOG.info("DB pool initialised (%d–%d connections)", minconn, maxconn)


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None
        _LOG.info("DB pool closed")


def get_conn() -> Any:
    if _pool is None:
        init_pool()
    assert _pool is not None
    return _pool.getconn()


def put_conn(conn: Any) -> None:
    if _pool is not None:
        _pool.putconn(conn)
