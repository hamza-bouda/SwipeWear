# Contracts Changelog

All breaking changes to shared schemas must be recorded here.
Increment `schema_version` in `contracts/interfaces.py` for breaking changes.

## v1.1 — 2026-07-20 — Hamza Bouda (KAN-16)
- ProductRecord moved to `contracts/product.py` (canonical definition).
- Added fields: `source_record_id`, `size_raw`, `size_eu`, `category`, `available`.
- Replaced `price_eur: float` with `price: float (gt=0)` + `currency: str`.
- Replaced `product_id: str` with `id: str`.
- Added `ProductSource` enum (ebay / awin / cj).
- Added Pydantic validators: price > 0, image_urls non-empty.
- `interfaces.py` now re-exports ProductRecord, ProductCondition, ProductSource from product.py.

## v1.0 — 2026-07-20 — Hamza Bouda (KAN-15)
- Initial schemas: InteractionEvent, UserPreferenceProfile, ProductRecord,
  CandidateSet, RankedItem, FeedItem, FeedResult, ModuleTrace.
