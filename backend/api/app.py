from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from api.config import app_env
from api.db import close_pool, get_conn, init_pool, put_conn
from api.errors import unhandled_exception_handler
from api.routers import (
    alerts, auth, billing, debug, drop, events, feed,
    ladder, notifications, onboarding, products, profile, saves,
    share, watcher_admin,
)


_LOG = logging.getLogger("swipewear.api.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_pool()
    yield
    close_pool()


app = FastAPI(
    title="SwipeWear API",
    version="0.1.0",
    description="B2C second-hand fashion discovery — feed, swipe events, profile & onboarding.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(auth.router)
app.include_router(billing.router)
app.include_router(alerts.router)
app.include_router(notifications.router)
app.include_router(drop.router)
app.include_router(feed.router)
app.include_router(ladder.router)
app.include_router(share.router)
app.include_router(events.router)
app.include_router(products.router)
app.include_router(saves.router)
app.include_router(profile.router)
app.include_router(onboarding.router)
app.include_router(watcher_admin.router)
app.include_router(debug.router)


@app.get("/health", tags=["infra"])
def health(response: Response, deep: bool = False):
    """Health probe backing railway.toml's healthcheckPath.

    It used to answer {"status": "ok"} unconditionally, so a deployment whose
    database was unreachable or misconfigured was still declared healthy and
    put in front of users. The check now fails when the app cannot do the one
    thing every endpoint needs.

    `?deep=true` adds catalogue counts. They are kept off the default path
    because the probe runs constantly and a feed outage caused by an empty
    index is an operator question, not a restart trigger.
    """
    checks: dict[str, bool] = {}
    details: dict[str, object] = {}

    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
            checks["database"] = True
            if deep:
                cur.execute(
                    "SELECT count(*) FROM products WHERE available = true"
                )
                details["products_available"] = cur.fetchone()[0]
                cur.execute("SELECT count(*) FROM product_embeddings")
                details["products_indexed"] = cur.fetchone()[0]
    except Exception:
        checks["database"] = False
        _LOG.exception("Health check failed to reach the database")
    finally:
        if conn is not None:
            put_conn(conn)

    healthy = all(checks.values())
    response.status_code = 200 if healthy else 503
    return {
        "status": "ok" if healthy else "degraded",
        "environment": app_env(),
        "version": app.version,
        "checks": checks,
        **({"details": details} if deep else {}),
    }
