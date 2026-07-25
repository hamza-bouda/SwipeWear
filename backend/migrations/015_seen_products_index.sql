-- Migration 015 — index for excluding already-seen products (KAN-88)
--
-- Measured before this change: a user who swiped through a 15-card feed and
-- reloaded got 13 of the same 15 cards back. Nothing anywhere excluded what
-- the user had already seen, which for a swipe app means the deck never
-- advances however large the catalogue is.
--
-- The retriever now filters with NOT EXISTS on (user_id, product_id). The two
-- existing indexes are both (user_id, timestamp), which cannot serve that
-- lookup — without this index the subquery scans every event a user ever
-- produced, on every feed request.

CREATE INDEX IF NOT EXISTS interaction_events_user_product_idx
    ON interaction_events (user_id, product_id);
