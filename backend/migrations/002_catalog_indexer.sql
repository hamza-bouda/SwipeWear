-- Migration 002 - catalogue embedding indexer support (KAN-29)

ALTER TABLE products
    ADD COLUMN IF NOT EXISTS embedding_version TEXT,
    ADD COLUMN IF NOT EXISTS needs_reindex BOOLEAN NOT NULL DEFAULT TRUE;

ALTER TABLE product_embeddings
    ADD COLUMN IF NOT EXISTS indexed_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE UNIQUE INDEX IF NOT EXISTS uq_product_embeddings_product_id
    ON product_embeddings (product_id);
