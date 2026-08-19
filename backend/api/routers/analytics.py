from __future__ import annotations

import json
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, status

from api.auth import get_current_user_id
from api.db import get_conn, put_conn
from api.schemas import AnalyticsEventRequest, AnalyticsEventResponse


router = APIRouter(prefix="/analytics", tags=["analytics"])

_INSERT_ANALYTICS_EVENT_SQL = """\
INSERT INTO analytics_events (event_id, user_id, event_name, properties, occurred_at)
VALUES (%s, %s, %s, %s::jsonb, %s)
"""


@router.post("/events", response_model=AnalyticsEventResponse, status_code=status.HTTP_201_CREATED)
def post_analytics_event(
    body: AnalyticsEventRequest,
    user_id: UUID = Depends(get_current_user_id),
) -> AnalyticsEventResponse:
    """Record a product metric for the authenticated server-issued identity.

    This endpoint is intentionally best-effort from the mobile client. A
    failed metric must never block browsing, swiping, or an outbound purchase.
    """
    event_id = uuid4()
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(
                _INSERT_ANALYTICS_EVENT_SQL,
                (
                    str(event_id),
                    str(user_id),
                    body.name,
                    json.dumps(body.properties),
                    body.occurred_at,
                ),
            )
        conn.commit()
    finally:
        if conn is not None:
            put_conn(conn)

    return AnalyticsEventResponse(event_id=event_id)
