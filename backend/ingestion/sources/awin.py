"""Awin affiliate network connector — new-condition products.

Credentials (never in code — read from environment):
    AWIN_API_TOKEN     Publisher API token
    AWIN_PUBLISHER_ID  Publisher (site) ID
"""
from __future__ import annotations

import logging
import os
from typing import Any

import requests

_LOG = logging.getLogger("swipewear.ingestion.awin")

_BASE_URL = "https://api.awin.com"
_PRODUCT_DATA_PATH = "/publishers/{publisher_id}/productdata/"


class AwinSource:
    """Awin Publisher API connector for new-condition affiliate products.

    Implements ingestion.interfaces.Source.
    All products returned have condition='new' (Awin carries new retail only).
    The affiliate tracking URL is provided directly by Awin in aw_deep_link.
    """

    def __init__(
        self,
        api_token: str | None = None,
        publisher_id: str | None = None,
        *,
        session: requests.Session | None = None,
    ) -> None:
        self._api_token = api_token or os.environ["AWIN_API_TOKEN"]
        self._publisher_id = publisher_id or os.environ["AWIN_PUBLISHER_ID"]
        self._session = session or requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {self._api_token}",
            "Accept": "application/json",
        })

    # ── Public interface ────────────────────────────────────────────────────

    def fetch(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search Awin products and return raw normalised dicts.

        filters keys (all optional):
            limit          int  — max results (default 100, max 1000)
            language       str  — product language (default 'fr')
            advertiser_id  str  — restrict to one advertiser/merchant
            min_price      float
            max_price      float
        """
        filters = filters or {}
        params: dict[str, Any] = {
            "keyword": query,
            "offset": 0,
            "limit": min(int(filters.get("limit", 100)), 1000),
            "language": filters.get("language", "fr"),
        }
        if filters.get("advertiser_id"):
            params["advertiser_id"] = filters["advertiser_id"]
        if filters.get("min_price") is not None:
            params["min_price"] = filters["min_price"]
        if filters.get("max_price") is not None:
            params["max_price"] = filters["max_price"]

        url = _BASE_URL + _PRODUCT_DATA_PATH.format(publisher_id=self._publisher_id)
        resp = self._session.get(url, params=params, timeout=15)
        resp.raise_for_status()

        products: list[dict[str, Any]] = resp.json().get("data", [])
        _LOG.info(
            "Awin fetch complete",
            extra={"pipe_module": "ingestion.awin", "query": query, "n_results": len(products)},
        )
        return [self._map_item(p) for p in products]

    # ── Private helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _map_item(item: dict[str, Any]) -> dict[str, Any]:
        """Map a raw Awin product dict to a normalised raw dict."""
        merchant_id = item.get("merchant_id")
        product_id = item.get("product_id") or item.get("merchant_product_id") or ""
        item_id = f"{merchant_id}-{product_id}" if merchant_id and product_id else str(product_id)

        price_raw = item.get("search_price") or "0"
        try:
            price = float(str(price_raw).replace(",", "."))
        except (ValueError, TypeError):
            price = 0.0

        image_url: str = item.get("aw_image_url") or ""

        return {
            "item_id": item_id,
            "title": item.get("product_name", ""),
            "price": price,
            "currency": (item.get("currency") or "EUR").upper(),
            "condition": "new",
            "image_urls": [image_url] if image_url else [],
            "listing_url": item.get("aw_deep_link", ""),
            "source": "awin",
            "brand": item.get("brand_name") or None,
            "category": item.get("category_name") or None,
        }
