-- Migration 013 — add model column to products (KAN-87)
-- ProductRecord.model exists in the contract and normalize() already fills it,
-- but 001_init.sql never created the column. Without it the price ladder can
-- only ever return MatchConfidence.similar: _compute_confidence requires both
-- brand AND model to match, so "the same item, cheaper elsewhere" — the whole
-- premise of the ladder — was unreachable in production.
-- Same class of omission as 003 (event_count) and 004 (available).
--
-- eBay does not expose a model field, so rows land NULL until title parsing
-- (GLiNER) populates it; the column is what makes that enrichment possible.

ALTER TABLE products
    ADD COLUMN IF NOT EXISTS model TEXT;
