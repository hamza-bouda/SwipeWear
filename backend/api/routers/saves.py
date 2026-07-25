"""The wardrobe — products the user kept, rebuilt from the event log.

"Mon dressing" lived entirely in a React useState, so it emptied on every app
restart and never reached the server. The saves themselves were being recorded
as InteractionEvents all along; nothing ever read them back.

The list is derived, not stored: the event log is the source of truth
(blueprint §6), so a product is in the wardrobe when its most recent
save/unsave event is a save.
"""
from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from api.auth import get_current_user_id
from api.db import get_conn, put_conn
from api.schemas import SavesResponse
from contracts.product import ProductCondition, ProductRecord, ProductSource

_LOG = logging.getLogger("swipewear.api.saves")

router = APIRouter(prefix="/saves", tags=["saves"])

_COLUMNS = [
    "id", "source", "source_record_id", "title", "brand", "model", "gender",
    "price", "condition", "size_raw", "size_eu",
    "category", "image_urls", "available", "embedding_version", "listing_url",
]

# DISTINCT ON keeps one row per product — the latest save/unsave — and the
# outer filter keeps only those whose latest is a save. Comparing counts of
# saves against unsaves would get the order wrong: save, unsave, save again
# is one save, not a tie.
_QUERY = """\
SELECT {columns}
FROM (
    SELECT DISTINCT ON (ie.product_id) ie.product_id, ie.event_type, ie.timestamp
    FROM interaction_events AS ie
    WHERE ie.user_id = %(user_id)s
      AND ie.event_type IN ('save', 'unsave')
      AND ie.product_id IS NOT NULL
    ORDER BY ie.product_id, ie.timestamp DESC
) AS latest
JOIN products AS p ON p.id = latest.product_id
WHERE latest.event_type = 'save'
ORDER BY latest.timestamp DESC
LIMIT %(limit)s"""


def _row_to_product(row: tuple) -> ProductRecord:
    data = dict(zip(_COLUMNS, row))
    data["source"] = ProductSource(data["source"])
    data["condition"] = ProductCondition(data["condition"])
    data["price"] = float(data["price"])
    data["image_urls"] = list(data["image_urls"] or [])
    # The column holds the raw seller URL; affiliate deep links are derived
    # from it at serve time.
    data["affiliate_url"] = data.pop("listing_url", None)
    return ProductRecord(**data)


@router.get("", response_model=SavesResponse)
def get_saves(
    limit: int = 200,
    user_id: UUID = Depends(get_current_user_id),
):
    """Return the user's wardrobe, most recently saved first."""
    conn = None
    try:
        conn = get_conn()
        query = _QUERY.format(columns=", ".join(f"p.{c}" for c in _COLUMNS))
        with conn.cursor() as cur:
            cur.execute(query, {"user_id": str(user_id), "limit": limit})
            rows = cur.fetchall()
        return SavesResponse(products=[_row_to_product(r) for r in rows])
    except Exception:
        # An empty wardrobe and a failed query look identical to the client if
        # this returns [], and the user would think their saves were lost.
        _LOG.error("Failed to load the wardrobe for %s", user_id, exc_info=True)
        if conn is not None:
            try:
                conn.rollback()
            except Exception:  # noqa: BLE001 - never mask the original failure
                pass
        raise HTTPException(
            status_code=503,
            detail={
                "error": "saves_unavailable",
                "message": "Impossible de charger ton dressing.",
            },
        )
    finally:
        if conn is not None:
            put_conn(conn)
