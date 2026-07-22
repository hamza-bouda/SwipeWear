-- Migration 005 -- widen embeddings from 512 to 768 dimensions (KAN-77)
--
-- The real Marqo-FashionSigLIP model (via OpenCLIP) outputs 768-dim vectors,
-- not the 512 assumed in 001_init.sql. Nobody had caught this because no
-- real embedding had ever actually been computed before (embeddings tests
-- mock the model entirely) -- confirmed by running the real pipeline for
-- KAN-33's style archetypes.
--
-- Safe as a drop-and-recreate today: no real product embeddings exist yet
-- (ingestion has only ever been tested against a mocked embedding service).
-- This would NOT be safe post-launch, once real data exists.

DROP INDEX IF EXISTS idx_product_embeddings_hnsw;

ALTER TABLE product_embeddings
    ALTER COLUMN embedding TYPE vector(768);

CREATE INDEX IF NOT EXISTS idx_product_embeddings_hnsw
    ON product_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
