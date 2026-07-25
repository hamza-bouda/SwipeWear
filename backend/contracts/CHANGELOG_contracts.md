# Contracts Changelog

## v2.2 — 2026-07-25 — Hamza Bouda (KAN-89)
- `contracts/events.py`: added `EventType.unsave = "unsave"`.
  Non-breaking — new enum value, like `ProductSource.vinted` in v2.0.
  The wardrobe ("Mon dressing") is derived from the event log, which is the
  source of truth (§6), so removing a saved item has to be recorded as an
  event. With only `save` available the list could grow but never shrink, and
  the heart toggle in the app was therefore local-only state that vanished on
  restart and never reached the server at all.

## v2.1 — 2026-07-25 — Hamza Bouda (KAN-88)
- `contracts/profile.py`: added `Gender` enum (men | women | unisex) and
  `HardConstraints.gender: Gender | None = None`.
  Non-breaking — new optional field defaulting to None, which preserves the
  current behaviour of showing everything to everybody.
  The feed was mixing menswear and womenswear with no way to say which you
  wanted. It belongs in the hard constraints so the filter is applied during
  retrieval: filtering the candidate set afterwards would spend the pool on
  items that are then discarded and leave the deck short.
  `unisex` is a value, not an absence — those items must reach every feed —
  while a product whose gender was never recorded is NULL and is also shown,
  the same rule already used for size (28 295 of 50 927 ingested titles say
  neither "homme" nor "femme").
- `contracts/product.py`: added `ProductSource.vinted = "vinted"`.
  Non-breaking — new enum value; existing sources (ebay, awin, cj, etsy) unaffected.
  Required for the isolated Vinted watcher which writes products with source='vinted'.

## v1.9 — 2026-07-23 — Hamza Bouda (KAN-70)
- `contracts/alerts.py`: added `Alert.reference_dinov2_embedding: list[float] | None` (default None).
  Non-breaking — new optional field; existing alerts unaffected.
  Stores DINOv2 CLS-token embedding computed at alert creation time for specific_item alerts.

## v1.8 — 2026-07-23 — Hamza Bouda (KAN-69)
- `contracts/alerts.py` (new): `Alert`, `AlertType` (specific_item | style),
  `AlertConstraints` (max_price_eur, sizes, min_condition), `AlertStatus` (active | paused).
- `FREE_ALERT_LIMIT = 3` constant (free tier cap, Premium argument).
- Non-breaking addition — no existing contracts modified.

All breaking changes to shared schemas must be recorded here.
Increment `schema_version` in `contracts/interfaces.py` for breaking changes.

## v1.7 — 2026-07-22 — rachid iraauan (KAN-77)
- StyleVectors: `vector_dim` default corrected from `512` to `768`.
  Breaking in practice (any code assuming 512-length vectors), but not
  breaking for the schema shape itself (still an int field) — no real
  embeddings existed yet under the old assumption, so no live data migration
  is needed. The real Marqo-FashionSigLIP model outputs 768-dim vectors;
  512 had never been verified against an actual model run. See also:
  `embeddings/interfaces.py::VECTOR_DIM`, `migrations/005_embedding_dim_768.sql`.

## v1.6 — 2026-07-21 — Hamza Bouda (KAN-76)
- ProductSource: added `etsy` variant.
  Non-breaking — new enum value; existing sources unaffected.
  Required for Etsy Open API v3 connector (vintage & second-hand fashion).

## v1.5 — 2026-07-20 — Hamza Bouda (KAN-25)
- ProductRecord: added `enriched_attrs: dict[str, str]` (default `{}`).
  Non-breaking — optional field; existing records and tests unaffected.
  Populated by `ingestion/enricher.py::TitleEnricher` with GLiNER entity labels.

## v1.4 — 2026-07-20 — Hamza Bouda (KAN-19)
- Pipeline contracts moved to `contracts/pipeline.py`.
- RecoRequest (new): user_profile, n_results, session_intent, request_id.
- CandidateSet: added hard_filters_applied, fallback_used, removed user_id.
- RankedFeed (replaces FeedResult): items, diversity_applied, fallback_used.
- RankedItem: added price_ladder (list[PriceLadderEntry]) — échelle de prix F07.
- PriceLadderEntry (new): url, price_eur, source, is_new, affiliate_url.
- Explanation (new): product_id, reasons, evidence_refs, grounded, editable_tags, sentence.
- ModuleTrace moved to pipeline.py (was inline in interfaces.py).
- interfaces.py now re-exports all pipeline types from pipeline.py.
- Removed SchemaVersion enum — each model carries schema_version: int directly.

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
