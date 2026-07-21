-- Migration 004 — add available column to products (KAN-76)
-- The hard_filter always applies WHERE available = true, but the column was
-- missing from 001_init.sql.  Default true matches ProductRecord contract.

ALTER TABLE products
    ADD COLUMN IF NOT EXISTS available BOOLEAN NOT NULL DEFAULT TRUE;
