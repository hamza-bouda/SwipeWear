"""eBay Browse API v1 connector — second-hand product search.

Credentials (never in code — read from environment):
    EBAY_CLIENT_ID      OAuth app client ID
    EBAY_CLIENT_SECRET  OAuth app client secret
    EBAY_ENV            'sandbox' (default) or 'production'
    EBAY_IMAGE_SIZE     eBay image variant to request (default '500')
"""
from __future__ import annotations

import logging
import os
import re
import time
from typing import Any

import requests

logger = logging.getLogger("swipewear.ingestion.ebay")

_OAUTH_URL = {
    "sandbox": "https://api.sandbox.ebay.com/identity/v1/oauth2/token",
    "production": "https://api.ebay.com/identity/v1/oauth2/token",
}
_SEARCH_URL = {
    "sandbox": "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search",
    "production": "https://api.ebay.com/buy/browse/v1/item_summary/search",
}

# eBay condition IDs → SwipeWear ProductCondition values
_CONDITION_MAP: dict[str, str] = {
    "NEW": "new",
    "LIKE_NEW": "like_new",
    "VERY_GOOD": "like_new",
    "GOOD": "good",
    "ACCEPTABLE": "fair",
    "FOR_PARTS_OR_NOT_WORKING": "fair",
    "USED": "good",
}

_DAILY_LIMIT = 5_000
_OAUTH_SCOPE = "https://api.ebay.com/oauth/api_scope"

# eBay refuses offset + limit > 10 000 on a single query, so one query can
# never yield more than that many items — breadth has to come from more
# queries, not deeper paging.
MAX_OFFSET = 10_000
MAX_LIMIT = 200

# eBay serves any image at s-l<N>.jpg. The API hands back s-l225, whose short
# edge (164 px) is below FashionSigLIP's 224 px input: the preprocessor would
# upscale it and embed blur. s-l500 clears 224 on both edges at ~67 KB, where
# s-l1600 costs ~505 KB for detail the model discards when it resizes anyway.
_IMAGE_SIZE = os.getenv("EBAY_IMAGE_SIZE", "500")
_IMAGE_SIZE_RE = re.compile(r"/s-l\d+\.jpg$")


def _upgrade_image_url(url: str) -> str:
    """Rewrite an eBay image URL to the configured resolution variant."""
    return _IMAGE_SIZE_RE.sub(f"/s-l{_IMAGE_SIZE}.jpg", url)


class _TokenCache:
    """In-process OAuth access-token cache (client credentials grant)."""

    def __init__(self) -> None:
        self._token: str | None = None
        self._expires_at: float = 0.0

    def get(
        self,
        client_id: str,
        client_secret: str,
        env: str,
        session: requests.Session,
    ) -> str:
        if self._token and time.time() < self._expires_at - 30:
            return self._token
        resp = session.post(
            _OAUTH_URL[env],
            auth=(client_id, client_secret),
            data={"grant_type": "client_credentials", "scope": _OAUTH_SCOPE},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._expires_at = time.time() + data.get("expires_in", 7200)
        return self._token  # type: ignore[return-value]


class EbaySource:
    """eBay Browse API v1 connector.  Implements ingestion.interfaces.Source."""

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        env: str | None = None,
        *,
        session: requests.Session | None = None,
    ) -> None:
        self._client_id = client_id or os.environ["EBAY_CLIENT_ID"]
        self._client_secret = client_secret or os.environ["EBAY_CLIENT_SECRET"]
        self._env = (env or os.getenv("EBAY_ENV", "sandbox")).lower()
        if self._env not in _OAUTH_URL:
            raise ValueError(f"EBAY_ENV must be 'sandbox' or 'production', got {self._env!r}")
        self._session = session or requests.Session()
        self._token_cache = _TokenCache()
        self._daily_calls = 0

    # ── Public interface ────────────────────────────────────────────────────

    def fetch(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search eBay items and return raw normalised dicts.

        Respects the 5 000 req/day sandbox limit and retries on 429.

        Supported filters: limit, offset, category_id, min_price, max_price.
        """
        filters = filters or {}
        limit = min(int(filters.get("limit", 50)), MAX_LIMIT)

        token = self._token_cache.get(
            self._client_id, self._client_secret, self._env, self._session
        )
        headers = {
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_FR",
            "Content-Type": "application/json",
        }
        params = self._build_params(query, filters, limit)

        payload = self._get_with_retry(_SEARCH_URL[self._env], headers=headers, params=params)

        self._daily_calls += 1
        if self._daily_calls >= _DAILY_LIMIT:
            logger.warning(
                "eBay daily call limit reached",
                extra={"pipe_module": "ingestion.ebay", "daily_calls": self._daily_calls},
            )

        items = payload.get("itemSummaries", [])
        logger.info(
            "eBay fetch complete",
            extra={"pipe_module": "ingestion.ebay", "query": query, "n_results": len(items)},
        )
        return [self._map_item(item) for item in items]

    # ── Private helpers ─────────────────────────────────────────────────────

    def _build_params(
        self, query: str, filters: dict[str, Any], limit: int
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "q": query,
            "limit": limit,
            "fieldgroups": "MATCHING_ITEMS",
        }
        offset = int(filters.get("offset", 0))
        if offset:
            # Past the cap eBay returns an error rather than an empty page,
            # which would abort a bulk run mid-query.
            if offset + limit > MAX_OFFSET:
                raise ValueError(
                    f"offset + limit must be <= {MAX_OFFSET}, "
                    f"got {offset} + {limit}"
                )
            params["offset"] = offset
        if filters.get("category_id"):
            params["category_ids"] = filters["category_id"]
        min_p = filters.get("min_price")
        max_p = filters.get("max_price")
        if min_p is not None or max_p is not None:
            params["filter"] = "price:[{min}..{max}],priceCurrency:EUR".format(
                min=min_p if min_p is not None else "",
                max=max_p if max_p is not None else "",
            )
        return params

    def _get_with_retry(
        self,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, Any],
        max_retries: int = 3,
    ) -> dict[str, Any]:
        backoff = 1.0
        for attempt in range(max_retries):
            resp = self._session.get(url, headers=headers, params=params, timeout=15)
            if resp.status_code == 429:
                retry_after = float(resp.headers.get("Retry-After", backoff))
                logger.warning(
                    "eBay 429 — backing off",
                    extra={
                        "pipe_module": "ingestion.ebay",
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
            f"eBay Browse API still returning 429 after {max_retries} retries"
        )

    @staticmethod
    def _map_item(item: dict[str, Any]) -> dict[str, Any]:
        """Map a raw eBay itemSummary to a normalised raw dict."""
        price_info = item.get("price", {})
        condition_raw = (
            item.get("condition", "USED").upper().replace(" ", "_")
        )
        images: list[str] = []
        if item.get("image"):
            images.append(item["image"]["imageUrl"])
        for extra in item.get("additionalImages", []):
            url = extra.get("imageUrl", "")
            if url and url not in images:
                images.append(url)
        if not images and item.get("thumbnailImages"):
            images = [img["imageUrl"] for img in item["thumbnailImages"]]
        images = [_upgrade_image_url(u) for u in images]

        cat_ids = item.get("categories", [])
        category_id = str(cat_ids[0]["categoryId"]) if cat_ids else None

        return {
            "item_id": item.get("itemId", ""),
            "title": item.get("title", ""),
            "price": float(price_info.get("value", 0)),
            "currency": price_info.get("currency", "EUR"),
            "condition": _CONDITION_MAP.get(condition_raw, "fair"),
            "image_urls": images,
            "listing_url": item.get("itemWebUrl", ""),
            "source": "ebay",
            "brand": item.get("brand"),
            "category_id": category_id,
            "size_raw": item.get("sizeType") or item.get("size"),
        }
