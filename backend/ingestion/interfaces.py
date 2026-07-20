from __future__ import annotations

from typing import Any, Protocol


class Source(Protocol):
    """Isolation interface for a product data source (eBay, Awin, CJ…).

    Each connector lives in ingestion/sources/<name>.py and implements this
    protocol.  Switching sources never touches the normalisation pipeline.
    """

    def fetch(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search the source and return a list of raw item dicts.

        Args:
            query:   Free-text search string (product name, category, …)
            filters: Optional key-value filters (limit, min_price, max_price,
                     category_id, …).  Connector-specific; unknown keys ignored.

        Returns:
            List of raw dicts with at least:
                item_id, title, price, currency, condition,
                image_urls, listing_url, source
        """
        ...
