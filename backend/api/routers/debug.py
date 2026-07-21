from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from api.auth import get_current_user_id
from api.trace_store import get
from contracts.trace import RequestTrace

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/trace/{trace_id}", response_model=RequestTrace)
def get_trace(
    trace_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
) -> RequestTrace:
    """Return only the caller's own trace; this endpoint is for development."""
    trace = get(trace_id)
    if trace is None or trace.user_id != user_id:
        raise HTTPException(status_code=404, detail="Trace not found")
    return trace

