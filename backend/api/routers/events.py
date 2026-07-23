from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Depends

from api.auth import get_current_user_id
from api.db import get_conn, put_conn
from api.schemas import EventRequest, EventResponse
from contracts.events import InteractionEvent
from preferences.fallback_updater import FallbackUpdater
from preferences.store import ProfileStore

router = APIRouter(prefix="/events", tags=["events"])

_updater = FallbackUpdater()

_INSERT_EVENT_SQL = """\
INSERT INTO interaction_events
    (event_id, user_id, product_id, event_type, payload, timestamp, schema_version)
VALUES
    (%s, %s, %s, %s, %s::jsonb, %s, %s)
ON CONFLICT (event_id) DO NOTHING
"""


def _persist_event(conn, event: InteractionEvent) -> None:
    with conn.cursor() as cur:
        cur.execute(
            _INSERT_EVENT_SQL,
            (
                str(event.event_id),
                str(event.user_id),
                event.product_id,
                event.event_type.value,
                json.dumps(event.payload),
                event.timestamp,
                event.schema_version,
            ),
        )
    conn.commit()


@router.post("", response_model=EventResponse, status_code=201)
def post_event(
    body: EventRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    event = InteractionEvent(
        user_id=user_id,
        product_id=body.product_id,
        event_type=body.event_type,
        payload=body.payload,
    )

    conn = None
    try:
        conn = get_conn()
        _persist_event(conn, event)
        store = ProfileStore(lambda: conn)
        profile = store.load(user_id)
        updated = _updater.apply(profile, event)
        store.save(updated)
    finally:
        if conn:
            put_conn(conn)

    return EventResponse(event_id=event.event_id)
