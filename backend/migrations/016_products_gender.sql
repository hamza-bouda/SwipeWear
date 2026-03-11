-- Migration 016 — add gender to products (KAN-88)
--
-- The feed mixed menswear and womenswear with no way for a shopper to say
-- which they wanted, so roughly half of every deck was irrelevant.
--
-- Three values, and NULL is a fourth state that matters:
--   'men' / 'women'  the item is cut for one of them
--   'unisex'         suits anybody, so it belongs in every feed
--   NULL             never recorded — also shown, because eBay item summaries
--                    rarely state it and excluding unknowns would discard most
--                    of the catalogue (the same rule migration 012 established
--                    for size).
--
-- The partial index carries the filter used at retrieval; NULL rows are
-- excluded from it since the query never looks them up by value.

ALTER TABLE products
    ADD COLUMN IF NOT EXISTS gender TEXT
        CHECK (gender IN ('men', 'women', 'unisex'));

CREATE INDEX IF NOT EXISTS products_gender_idx
    ON products (gender) WHERE gender IS NOT NULL;
