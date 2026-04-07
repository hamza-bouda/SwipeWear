"""Normalise a VintedListing into a dict ready for INSERT into products (KAN-72).

The output schema matches backend/migrations/001_init.sql exactly so the
watcher can write to the same products table as every other source.

No backend imports — this module is intentionally self-contained.
"""
from __future__ import annotations

import hashlib
from typing import Any

from watcher.models import VintedListing

# Vinted condition labels → backend ProductCondition values
_CONDITION_MAP: dict[str, str] = {
    "new_with_tags": "new",
    "new_without_tags": "new",
    "very_good": "like_new",
    "good": "good",
    "satisfactory": "fair",
}

_DEFAULT_CONDITION = "good"


def _stable_id(listing_id: str) -> str:
    """Deterministic product ID from Vinted listing ID."""
    return "vinted-" + hashlib.sha256(listing_id.encode()).hexdigest()[:16]


def normalise(listing: VintedListing) -> dict[str, Any]:
    """Return a dict suitable for upsert into the products table."""
    if not listing.image_urls:
        raise ValueError(f"Listing {listing.listing_id} has no images — skipping")

    condition = _CONDITION_MAP.get(listing.condition, _DEFAULT_CONDITION)

    return {
        "id": _stable_id(listing.listing_id),
        "source": "vinted",
        "source_record_id": listing.listing_id,
        "title": listing.title.strip(),
        "brand": listing.brand,
        "model": None,
        "price": listing.price_eur,
        "currency": listing.currency,
        "condition": condition,
        "size_raw": listing.size_label,
        "size_eu": listing.size_label,
        "category": listing.category or "fashion",
        "image_urls": listing.image_urls,
        "affiliate_url": listing.listing_url or None,
        "available": True,
        "enriched_attrs": {},
        "schema_version": 1,
        "embedding_version": None,
    }
