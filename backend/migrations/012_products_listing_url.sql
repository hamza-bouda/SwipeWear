-- Migration 012 — add listing_url to products (KAN-87)
-- normalize() already carries the seller's listing URL on ProductRecord, but
-- no column stored it, so every ingested link was dropped at persistence and
-- the app had nowhere to send a user who taps a product.
-- Affiliate deep links are derived from this raw URL at serve time
-- (ingestion/affiliate.py); the stored value stays the plain listing URL so a
-- change of affiliate program never requires re-ingesting the catalogue.

ALTER TABLE products
    ADD COLUMN IF NOT EXISTS listing_url TEXT;
