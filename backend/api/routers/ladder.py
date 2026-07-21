from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from api.auth import get_current_user_id
from api.db import get_conn, put_conn
from contracts.pipeline import PriceLadder
from retrieval.interfaces import build_price_ladder

_LOG = logging.getLogger("swipewear.api.ladder")

router = APIRouter(prefix="/ladder", tags=["ladder"])


@router.get("/{product_id}", response_model=PriceLadder)
def get_price_ladder(
    product_id: str,
    max_results: int = 15,
    user_id=Depends(get_current_user_id),
):
    conn = None
    try:
        conn = get_conn()
        return build_price_ladder(
            product_id, lambda: conn, max_results=max_results,
        )
    except Exception:
        _LOG.warning(
            "Ladder unavailable for %s, returning empty", product_id,
            exc_info=True,
        )
        return PriceLadder(
            source_product_id=product_id, entries=[], latency_ms=0.0,
        )
    finally:
        if conn is not None:
            put_conn(conn)
