from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends

from api.auth import get_current_user_id
from api.db import get_conn, put_conn
from api.pipeline import build_orchestrator
from api.schemas import FeedResponse
from contracts.pipeline import Explanation, RankedItem, RecoRequest
from contracts.product import ProductCondition, ProductRecord, ProductSource
from ingestion.interfaces import ClickContext, build_affiliate_url
from preferences.interfaces import ProfileStore

_LOG = logging.getLogger("swipewear.api.feed")

router = APIRouter(prefix="/feed", tags=["feed"])

_MOCK_PRODUCTS = [
    ProductRecord(
        id=f"prod-{i}",
        source=ProductSource.ebay,
        source_record_id=f"ebay-{i}",
        title=title,
        brand=brand,
        price=price,
        currency="EUR",
        condition=ProductCondition.good,
        category="tops",
        image_urls=[f"https://picsum.photos/seed/{i}/400/600"],
    )
    for i, (title, brand, price) in enumerate(
        [
            ("Nike Air Max 90", "Nike", 65.0),
            ("Levi's 501 Original", "Levi's", 45.0),
            ("The North Face Nuptse", "The North Face", 120.0),
            ("Carhartt WIP Chore Coat", "Carhartt", 85.0),
            ("New Balance 550", "New Balance", 55.0),
            ("Stussy Basic Tee", "Stussy", 25.0),
            ("Dickies 874 Work Pant", "Dickies", 35.0),
            ("Patagonia Retro-X Jacket", "Patagonia", 95.0),
        ],
        start=1,
    )
]


def _get_mock_feed(n_results: int, cursor: str | None) -> FeedResponse:
    start = 0
    if cursor is not None:
        try:
            start = int(cursor)
        except ValueError:
            start = 0

    end = min(start + n_results, len(_MOCK_PRODUCTS))
    products = _MOCK_PRODUCTS[start:end]

    items = [
        RankedItem(
            product=p,
            final_score=1.0 - (i * 0.05),
            rank=start + i + 1,
            explanation=Explanation(
                product_id=p.id,
                editable_tags=[
                    value for value in (p.brand, p.category, p.condition.value)
                    if value
                ],
            ),
        )
        for i, p in enumerate(products)
    ]
    next_cursor = str(end) if end < len(_MOCK_PRODUCTS) else None
    return FeedResponse(items=items, next_cursor=next_cursor, fallback_used=True)


def _enrich_with_affiliate_urls(
    items: list[RankedItem], context: ClickContext,
) -> list[RankedItem]:
    enriched: list[RankedItem] = []
    for item in items:
        url = build_affiliate_url(item.product, context)
        if url and url != (item.product.affiliate_url or ""):
            product = item.product.model_copy(update={"affiliate_url": url})
            enriched.append(item.model_copy(update={"product": product}))
        else:
            enriched.append(item)
    return enriched


@router.get("", response_model=FeedResponse)
def get_feed(
    n_results: int = 30,
    cursor: str | None = None,
    user_id: UUID = Depends(get_current_user_id),
):
    conn = None
    try:
        conn = get_conn()
        profile_store = ProfileStore(lambda: conn)
        profile = profile_store.load(user_id)

        orchestrator = build_orchestrator(lambda: conn)
        request = RecoRequest(
            user_profile=profile,
            n_results=n_results,
        )
        ranked_feed = orchestrator.get_feed(request)

        items = _enrich_with_affiliate_urls(
            ranked_feed.items, ClickContext.feed,
        )

        next_cursor = None
        if cursor is not None:
            try:
                offset = int(cursor)
                if offset + n_results < len(items):
                    next_cursor = str(offset + n_results)
            except ValueError:
                pass

        return FeedResponse(
            items=items,
            next_cursor=next_cursor,
            fallback_used=ranked_feed.fallback_used,
        )

    except Exception:
        _LOG.warning(
            "Pipeline unavailable, falling back to mock feed", exc_info=True,
        )
        return _get_mock_feed(n_results, cursor)

    finally:
        if conn is not None:
            put_conn(conn)
