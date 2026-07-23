from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.db import close_pool, init_pool
from api.errors import unhandled_exception_handler
from api.routers import alerts, auth, debug, events, feed, ladder, notifications, onboarding, profile, watcher_admin


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
app.include_router(alerts.router)
app.include_router(notifications.router)
app.include_router(feed.router)
app.include_router(ladder.router)
app.include_router(events.router)
app.include_router(profile.router)
app.include_router(onboarding.router)
app.include_router(watcher_admin.router)
app.include_router(debug.router)


@app.get("/health", tags=["infra"])
def health():
    return {"status": "ok"}
