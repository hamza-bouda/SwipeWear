from __future__ import annotations

import json
import logging
from uuid import UUID

from fastapi import APIRouter, Depends

from api.auth import get_current_user_id
from api.db import get_conn, put_conn
from api.schemas import EventRequest, EventResponse
from contracts.events import InteractionEvent
from preferences.fallback_updater import FallbackUpdater
from preferences.store import ProfileStore

_LOG = logging.getLogger("swipewear.api.events")

router = APIRouter(prefix="/events", tags=["events"])

_updater = FallbackUpdater()

_FETCH_EMBEDDING_SQL = """\
SELECT embedding FROM product_embeddings WHERE product_id = %(product_id)s
LIMIT 1"""


def _load_product_embedding(conn, product_id: str) -> list[float] | None:
    """Fetch the swiped product's vector so the swipe can move the profile.

    preferences/updater.py reads the embedding from the event payload, which
    meant the mobile client was expected to upload 768 floats with every
    swipe. It does not, so vectors.positive stayed empty however much a user
    swiped: the profile never left cold start and the feed ran on the
    fallback retriever forever — no personalisation at all.

    It is deliberately not written back into interaction_events. The log keeps
    product_id and a replay re-reads the vector from product_embeddings, so
    re-indexing the catalogue under a new embedding version stays possible
    without rewriting history (blueprint §3.6, §5).
    """
    try:
        with conn.cursor() as cur:
            cur.execute(_FETCH_EMBEDDING_SQL, {"product_id": product_id})
            row = cur.fetchone()
    except Exception:  # noqa: BLE001 - a swipe must be recorded regardless
        _LOG.warning(
            "Could not load embedding for %s", product_id, exc_info=True,
        )
        return None
    if row is None or row[0] is None:
        return None
    raw = row[0]
    if isinstance(raw, str):
        return [float(v) for v in raw.strip("[]").split(",") if v]
    return [float(v) for v in raw]


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

        embedding = _load_product_embedding(conn, event.product_id)
        if embedding is not None:
            # Enriched only for the updater, not for the stored row.
            event = event.model_copy(update={
                "payload": {**event.payload, "product_embedding": embedding},
            })

        store = ProfileStore(lambda: conn)
        profile = store.load(user_id)
        updated = _updater.apply(profile, event)
        store.save(updated)
    finally:
        if conn:
            put_conn(conn)

    return EventResponse(event_id=event.event_id)
