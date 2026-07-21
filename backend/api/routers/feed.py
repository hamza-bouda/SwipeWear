from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from api.auth import get_current_user_id
from api.schemas import FeedResponse
from api.store import get_or_create_profile
from contracts.pipeline import RankedItem
from contracts.product import ProductCondition, ProductRecord, ProductSource

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


def _get_mock_feed(profile, n_results: int, cursor: str | None) -> FeedResponse:
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
        )
        for i, p in enumerate(products)
    ]
    next_cursor = str(end) if end < len(_MOCK_PRODUCTS) else None
    return FeedResponse(items=items, next_cursor=next_cursor)


@router.get("", response_model=FeedResponse)
def get_feed(
    n_results: int = 30,
    cursor: str | None = None,
    user_id: UUID = Depends(get_current_user_id),
):
    profile = get_or_create_profile(user_id)
    return _get_mock_feed(profile, n_results, cursor)
