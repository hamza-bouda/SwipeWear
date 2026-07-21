"""Etsy Open API v3 connector — vintage & second-hand fashion.

Credentials (never in code — read from environment):
    ETSY_API_KEY   Application keystring from etsy.com/developers
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any

import requests

_LOG = logging.getLogger("swipewear.ingestion.etsy")

_BASE_URL = "https://openapi.etsy.com/v3"
_SEARCH_PATH = "/application/listings/active"

_CLOTHING_TAXONOMY_ID = 1
_FASHION_TAXONOMY_IDS = {
    "clothing": 1,
    "shoes": 1429,
    "bags_purses": 1517,
    "accessories": 2,
}

_CONDITION_MAP: dict[str, str] = {
    "is_vintage": "good",
    "is_not_vintage_new": "new",
    "is_not_vintage_used": "good",
}


class EtsySource:
    """Etsy Open API v3 connector for vintage & second-hand fashion.

    Implements ingestion.interfaces.Source.
    Rate limit: 10 req/s per API key (very generous for MVP).
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        session: requests.Session | None = None,
    ) -> None:
        self._api_key = api_key or os.environ["ETSY_API_KEY"]
        self._session = session or requests.Session()
        self._session.headers.update({
            "x-api-key": self._api_key,
            "Accept": "application/json",
        })

    def fetch(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search Etsy listings and return raw normalised dicts.

        filters keys (all optional):
            limit          int   — max results (default 50, max 100)
            min_price      float — minimum price (USD — Etsy uses cents)
            max_price      float — maximum price (USD — Etsy uses cents)
            taxonomy_id    int   — Etsy taxonomy ID to narrow search
        """
        filters = filters or {}
        limit = min(int(filters.get("limit", 50)), 100)

        params: dict[str, Any] = {
            "keywords": query,
            "limit": limit,
            "sort_on": "score",
            "sort_order": "desc",
            "includes": "Images",
        }

        taxonomy_id = filters.get("taxonomy_id", _CLOTHING_TAXONOMY_ID)
        if taxonomy_id:
            params["taxonomy_id"] = taxonomy_id

        if filters.get("min_price") is not None:
            params["min_price"] = float(filters["min_price"])
        if filters.get("max_price") is not None:
            params["max_price"] = float(filters["max_price"])

        payload = self._get_with_retry(
            f"{_BASE_URL}{_SEARCH_PATH}", params=params,
        )

        results: list[dict[str, Any]] = payload.get("results", [])
        _LOG.info(
            "Etsy fetch complete",
            extra={
                "pipe_module": "ingestion.etsy",
                "query": query,
                "n_results": len(results),
            },
        )
        return [self._map_item(item) for item in results]

    def _get_with_retry(
        self,
        url: str,
        *,
        params: dict[str, Any],
        max_retries: int = 3,
    ) -> dict[str, Any]:
        backoff = 1.0
        for attempt in range(max_retries):
            resp = self._session.get(url, params=params, timeout=15)
            if resp.status_code == 429:
                retry_after = float(resp.headers.get("Retry-After", backoff))
                _LOG.warning(
                    "Etsy 429 — backing off",
                    extra={
                        "pipe_module": "ingestion.etsy",
                        "attempt": attempt + 1,
                        "retry_after_s": retry_after,
                    },
                )
                time.sleep(retry_after)
                backoff *= 2
                continue
            resp.raise_for_status()
            return resp.json()
        raise RuntimeError(
            f"Etsy API still returning 429 after {max_retries} retries"
        )

    @staticmethod
    def _map_item(item: dict[str, Any]) -> dict[str, Any]:
        """Map a raw Etsy listing to a normalised raw dict."""
        listing_id = str(item.get("listing_id", ""))

        price_data = item.get("price", {})
        amount = price_data.get("amount", 0)
        divisor = price_data.get("divisor", 100)
        price = amount / divisor if divisor else 0.0
        currency = price_data.get("currency_code", "USD")

        images: list[str] = []
        for img in item.get("images", []):
            url = img.get("url_fullxfull") or img.get("url_570xN") or ""
            if url:
                images.append(url)
        if not images:
            main_img = item.get("MainImage", {})
            url = main_img.get("url_fullxfull") or main_img.get("url_570xN") or ""
            if url:
                images.append(url)

        is_vintage = item.get("is_vintage", False)
        if is_vintage:
            condition = "good"
        elif item.get("when_made", "").startswith("20"):
            condition = "like_new"
        else:
            condition = "good"

        shop_name = item.get("shop", {}).get("shop_name", "")
        listing_url = f"https://www.etsy.com/listing/{listing_id}" if listing_id else ""

        taxonomy = item.get("taxonomy_path", [])
        category = None
        if taxonomy:
            category = taxonomy[-1] if isinstance(taxonomy[-1], str) else None

        return {
            "item_id": listing_id,
            "title": item.get("title", ""),
            "price": price,
            "currency": currency,
            "condition": condition,
            "image_urls": images,
            "listing_url": listing_url,
            "source": "etsy",
            "brand": shop_name or None,
            "category": category,
            "is_vintage": is_vintage,
        }
