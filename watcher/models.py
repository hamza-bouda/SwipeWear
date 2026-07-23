"""Raw Vinted listing data model (KAN-72).

Represents a single public Vinted listing as fetched. Only public fields
are stored — no seller personal data (name, profile ID, location beyond
country, ratings). See LEGAL_REVIEW.md for the full data-minimisation log.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class VintedListing:
    """A single Vinted listing as returned by the (unofficial) Vinted API."""

    listing_id: str
    title: str
    price_eur: float
    condition: str
    size_label: str | None
    brand: str | None
    category: str | None
    image_urls: list[str] = field(default_factory=list)
    # Direct link to the Vinted listing page (public, no auth required)
    listing_url: str = ""
    currency: str = "EUR"
