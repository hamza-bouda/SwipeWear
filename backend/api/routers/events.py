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

_FETCH_PRODUCT_SIGNALS_SQL = """\
SELECT e.embedding, p.brand, p.price
FROM products AS p
LEFT JOIN product_embeddings AS e ON e.product_id = p.id
WHERE p.id = %(product_id)s
LIMIT 1"""


def _load_product_signals(conn, product_id: str) -> dict:
    """Fetch catalogue signals needed to apply a mobile swipe.

    The mobile client deliberately sends only the product id. Resolve the
    embedding, brand and price beside the catalogue so the client cannot forge
    learning signals and does not need to upload 768 floats per swipe.

    Brand and price are persisted in the event payload for replay. The vector
    remains an apply-time enrichment: re-indexing the catalogue under a new
    embedding version can then rebuild the dense profile without rewriting the
    interaction log.
    """
    try:
        with conn.cursor() as cur:
            cur.execute(_FETCH_PRODUCT_SIGNALS_SQL, {"product_id": product_id})
            row = cur.fetchone()
    except Exception:  # noqa: BLE001 - a swipe must be recorded regardless
        _LOG.warning("Could not load product signals for %s", product_id, exc_info=True)
        return {}
    if row is None:
        return {}

    embedding = row[0]
    if isinstance(embedding, str):
        embedding = [float(v) for v in embedding.strip("[]").split(",") if v]
    elif embedding is not None:
        embedding = [float(v) for v in embedding]

    return {
        "product_embedding": embedding,
        "brand": row[1],
        "product_price_eur": float(row[2]) if row[2] is not None else None,
    }


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
        signals = _load_product_signals(conn, event.product_id)
        persisted_payload = dict(event.payload)
        for key in ("brand", "product_price_eur"):
            if signals.get(key) is not None:
                persisted_payload[key] = signals[key]
        persisted_event = event.model_copy(update={"payload": persisted_payload})
        _persist_event(conn, persisted_event)

        embedding = signals.get("product_embedding")
        if embedding is not None:
            # The vector is used by the updater but not stored in the event
            # log; the product id lets a replay use the current vector version.
            event = persisted_event.model_copy(update={
                "payload": {**persisted_payload, "product_embedding": embedding},
            })
        else:
            event = persisted_event

        store = ProfileStore(lambda: conn)
        profile = store.load(user_id)
        updated = _updater.apply(profile, event)
        store.save(updated)
    finally:
        if conn:
            put_conn(conn)

    return EventResponse(event_id=event.event_id)
