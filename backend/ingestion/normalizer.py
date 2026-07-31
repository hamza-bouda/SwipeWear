"""Normalisation: raw source dict → validated ProductRecord.

Single source of truth for all source-to-schema mappings.
No module downstream knows the raw format of eBay or Awin.
"""
from __future__ import annotations

from typing import Any

from contracts.product import ProductCondition, ProductRecord, ProductSource


class NormalizationError(ValueError):
    """Raised when a raw dict cannot be converted to a valid ProductRecord."""


# ── Currency conversion (MVP: fixed rates) ────────────────────────────────────
# To update rates: edit this dict or override via a config file.
_FX_TO_EUR: dict[str, float] = {
    "EUR": 1.0,
    "USD": 0.92,
    "GBP": 1.17,
    "CHF": 1.04,
    "SEK": 0.087,
    "DKK": 0.134,
    "NOK": 0.086,
    "PLN": 0.23,
    "CZK": 0.040,
}


def _to_eur(amount: float, currency: str) -> float:
    rate = _FX_TO_EUR.get(currency.upper())
    if rate is None:
        raise NormalizationError(f"Unsupported currency: {currency!r}")
    return round(amount * rate, 2)


# ── Size normalisation ────────────────────────────────────────────────────────
_LETTER_SIZES: dict[str, str] = {
    s: s for s in ("XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL", "XXXXL")
}
# EU clothing: 28–60, EU shoes: 34–50
_EU_SIZES: frozenset[str] = frozenset(str(n) for n in range(28, 62, 2)) | frozenset(
    str(n) for n in range(34, 52)
)


def _normalize_size(raw: str | None) -> tuple[str | None, str | None]:
    """Return (size_raw, size_eu) from an arbitrary size string."""
    if not raw:
        return None, None
    size_raw = raw.strip()
    cleaned = size_raw.upper()
    if cleaned in _LETTER_SIZES:
        return size_raw, _LETTER_SIZES[cleaned]
    if cleaned in _EU_SIZES:
        return size_raw, cleaned
    # "EU 42", "EU42"
    for prefix in ("EU ", "EU"):
        if cleaned.startswith(prefix):
            inner = cleaned[len(prefix):].strip()
            if inner in _EU_SIZES:
                return size_raw, inner
    return size_raw, None


# ── Condition mapping ─────────────────────────────────────────────────────────
_CONDITION_MAP: dict[str, ProductCondition] = {
    # eBay raw labels
    "NEW": ProductCondition.new,
    "LIKE_NEW": ProductCondition.like_new,
    "VERY_GOOD": ProductCondition.like_new,
    "GOOD": ProductCondition.good,
    "USED": ProductCondition.good,
    "ACCEPTABLE": ProductCondition.fair,
    "FOR_PARTS_OR_NOT_WORKING": ProductCondition.fair,
    # Already-normalised values (EbaySource pre-maps these)
    "new": ProductCondition.new,
    "like_new": ProductCondition.like_new,
    "good": ProductCondition.good,
    "fair": ProductCondition.fair,
}


def _normalize_condition(raw: str | None) -> ProductCondition:
    if not raw:
        return ProductCondition.good
    key = raw.strip().upper().replace(" ", "_")
    if key in _CONDITION_MAP:
        return _CONDITION_MAP[key]
    lower = raw.strip().lower()
    if lower in _CONDITION_MAP:
        return _CONDITION_MAP[lower]
    return ProductCondition.fair


# ── Category mapping ──────────────────────────────────────────────────────────
# eBay France category IDs → 5 internal MVP categories.
_EBAY_CAT_MAP: dict[str, str] = {
    # Sneakers / chaussures (eBay FR)
    "15709": "sneakers",    # Chaussures homme
    "63889": "sneakers",    # Chaussures femme
    "57929": "sneakers",    # Baskets
    # Vestes / manteaux
    "57988": "vestes",      # Vestes homme
    "57990": "vestes",      # Manteaux homme
    "57991": "vestes",      # Vestes femme
    "15724": "vestes",      # Manteaux femme
    # Jeans / pantalons
    "11483": "jeans",       # Jeans homme
    "15689": "jeans",       # Jeans femme
    "57994": "jeans",       # Pantalons
    # Tee-shirts / hauts
    "15687": "tee-shirts",  # Tee-shirts homme
    "53159": "tee-shirts",  # Tee-shirts femme
    "11484": "tee-shirts",  # Hauts
    # Accessoires
    "169291": "accessoires",
    "4251": "accessoires",
    "281": "accessoires",
    "260": "accessoires",
}
_VALID_CATEGORIES = frozenset(
    {"sneakers", "vestes", "jeans", "tee-shirts", "accessoires"}
)
_CATEGORY_KEYWORDS: list[tuple[list[str], str]] = [
    (["sneaker", "basket", "chaussure", "shoe", "trainer"], "sneakers"),
    (["veste", "manteau", "jacket", "coat", "blouson"], "vestes"),
    (["jean", "denim", "pantalon", "trouser", "chino"], "jeans"),
    (["tee-shirt", "t-shirt", "tshirt", "polo", "top", "blouse"], "tee-shirts"),
]


def _normalize_category(cat_id: str | None, category: str | None, title: str) -> str:
    # 1. Known eBay category ID
    if cat_id and cat_id in _EBAY_CAT_MAP:
        return _EBAY_CAT_MAP[cat_id]
    # 2. Already an internal category value
    if category and category.lower() in _VALID_CATEGORIES:
        return category.lower()
    # 3. Title keyword fallback
    title_lower = title.lower()
    for keywords, cat in _CATEGORY_KEYWORDS:
        if any(kw in title_lower for kw in keywords):
            return cat
    return "accessoires"


# ── Public API ────────────────────────────────────────────────────────────────

def normalize(source: str, raw: dict[str, Any]) -> ProductRecord:
    """Convert a raw source dict to a validated ProductRecord.

    Args:
        source: Source identifier ('ebay', 'awin', 'cj').
        raw:    Raw dict as returned by a Source.fetch() connector.
                Expected keys (eBay connector): item_id, title, price,
                currency, condition, image_urls, listing_url.

    Returns:
        A fully-validated ProductRecord (Pydantic v2).

    Raises:
        NormalizationError: If required fields are missing or cannot be
                            converted to a valid ProductRecord.
    """
    try:
        product_source = ProductSource(source)
    except ValueError:
        raise NormalizationError(f"Unknown source: {source!r}")

    item_id = (raw.get("item_id") or raw.get("id") or "").strip()
    if not item_id:
        raise NormalizationError("Missing required field: 'item_id'")

    title = (raw.get("title") or "").strip()
    if not title:
        raise NormalizationError(f"Missing required field: 'title' (item_id={item_id!r})")

    raw_price = raw.get("price")
    if raw_price is None:
        raise NormalizationError(f"Missing required field: 'price' (item_id={item_id!r})")
    try:
        price_val = float(raw_price)
    except (TypeError, ValueError):
        raise NormalizationError(
            f"Invalid 'price': {raw_price!r} (item_id={item_id!r})"
        )
    if price_val <= 0:
        raise NormalizationError(
            f"'price' must be > 0, got {price_val} (item_id={item_id!r})"
        )

    currency = (raw.get("currency") or "EUR").strip().upper()
    try:
        price_eur = _to_eur(price_val, currency)
    except NormalizationError as exc:
        raise NormalizationError(
            f"{exc} (item_id={item_id!r})"
        ) from exc

    image_urls: list[str] = raw.get("image_urls") or []
    if not image_urls:
        raise NormalizationError(
            f"'image_urls' must be non-empty (item_id={item_id!r})"
        )

    condition = _normalize_condition(raw.get("condition"))
    size_raw, size_eu = _normalize_size(raw.get("size_raw") or raw.get("size"))
    category = _normalize_category(
        raw.get("category_id"),
        raw.get("category"),
        title,
    )

    try:
        return ProductRecord(
            id=f"{source}-{item_id}",
            source=product_source,
            source_record_id=item_id,
            title=title,
            price=price_eur,
            currency="EUR",
            condition=condition,
            category=category,
            image_urls=image_urls,
            size_raw=size_raw,
            size_eu=size_eu,
            affiliate_url=raw.get("listing_url") or raw.get("affiliate_url"),
            brand=raw.get("brand") or None,
            model=raw.get("model") or None,
        )
    except Exception as exc:
        raise NormalizationError(
            f"ProductRecord validation failed for item_id={item_id!r}: {exc}"
        ) from exc
