"""Database connection pool for FastAPI — shared across all endpoints."""
from __future__ import annotations

import logging
import os
from typing import Any

from psycopg2 import pool

from api.config import ConfigurationError, is_production

_LOG = logging.getLogger("swipewear.api.db")

_pool: pool.SimpleConnectionPool | None = None


_DEV_DATABASE_URL = "postgresql://swipewear:swipewear_dev@localhost:5432/swipewear"


def _get_database_url() -> str:
    """Return the DSN, refusing to guess one in production.

    The hardcoded localhost fallback is a development convenience that must
    not survive a deploy: an unset DATABASE_URL would otherwise send a
    production instance looking for a database on its own loopback, and the
    connection error that follows names the wrong problem entirely.

    It is also why five integration tests failed permanently — the fallback
    pins port 5432 while the project's compose file publishes ${POSTGRES_PORT},
    which is 5433 locally.
    """
    url = os.environ.get("DATABASE_URL")
    if url and url.strip():
        return url
    if is_production():
        raise ConfigurationError(
            "DATABASE_URL is not set. Refusing to start in production with "
            "the localhost development fallback."
        )
    _LOG.warning(
        "DATABASE_URL is not set — falling back to %s", _DEV_DATABASE_URL,
    )
    return _DEV_DATABASE_URL


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
