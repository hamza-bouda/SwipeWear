from __future__ import annotations

from fastapi import FastAPI

from api.errors import unhandled_exception_handler
from api.routers import auth, events, feed, onboarding, profile

app = FastAPI(
    title="SwipeWear API",
    version="0.1.0",
    description="B2C second-hand fashion discovery — feed, swipe events, profile & onboarding.",
)

app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(auth.router)
app.include_router(feed.router)
app.include_router(events.router)
app.include_router(profile.router)
app.include_router(onboarding.router)


@app.get("/health", tags=["infra"])
def health():
    return {"status": "ok"}
