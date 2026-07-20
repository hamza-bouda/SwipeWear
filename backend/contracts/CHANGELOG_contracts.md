# Contracts Changelog

All breaking changes to shared schemas must be recorded here.
Increment `schema_version` in `contracts/interfaces.py` for breaking changes.

## v1.3 — 2026-07-20 — Hamza Bouda (KAN-18)
- InteractionEvent moved to `contracts/events.py` (canonical definition).
- Added EventType enum: swipe_right, swipe_left_style, swipe_left_price, save, open, edit_preference.
- Replaced SwipeDirection + action field with EventType + payload (free-form JSONB).
- Removed session_id field (not needed at contract level).
- Added `preferences/_event_replay.py`: in-memory replay_events_in_memory().
- SQL migration: `migrations/001_interaction_events.sql`.
- `interfaces.py` re-exports EventType, InteractionEvent from events.py.

## v1.2 — 2026-07-20 — Hamza Bouda (KAN-17)
- UserPreferenceProfile moved to `contracts/profile.py` (canonical 3-layer definition).
- Layer 1 HardConstraints: added `excluded_conditions`.
- Layer 2 EditablePreferences (new): `liked_brands`, `rejected_brands`, `locked_attributes`.
- Layer 3 StyleVectors (new): `positive` + `negative` vectors, `embedding_version`, `vector_dim`.
- Removed `StyleVector` (single vector) — replaced by `StyleVectors` (pos + neg).
- Added `is_cold_start` property.
- `interfaces.py` now re-exports all profile types from profile.py.

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
