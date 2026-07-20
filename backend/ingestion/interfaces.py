from __future__ import annotations
from typing import AsyncIterator
from contracts.interfaces import ProductRecord

async def fetch_products(
    source: str,
    query: str,
    max_results: int = 100,
) -> AsyncIterator[ProductRecord]:
    # source in: "ebay", "awin", "cj". Called only by orchestration.
    raise NotImplementedError
