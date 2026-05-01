from __future__ import annotations

from fastapi import APIRouter, Depends

from api.auth import get_current_user_id
from contracts.pipeline import PriceLadder

router = APIRouter(prefix="/ladder", tags=["ladder"])


_MOCK_LADDER = PriceLadder(
    source_product_id="prod-1",
    entries=[],
    latency_ms=0.0,
)


@router.get("/{product_id}", response_model=PriceLadder)
def get_price_ladder(
    product_id: str,
    max_results: int = 15,
    user_id=Depends(get_current_user_id),
):
    return PriceLadder(
        source_product_id=product_id,
        entries=[],
        latency_ms=0.0,
    )
