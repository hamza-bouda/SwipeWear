-- Migration 001 — initial schema
-- SwipeWear backend: products, embeddings (HNSW/cosine), events, profiles
-- interaction_events schema mirrors contracts/events.py InteractionEvent

CREATE EXTENSION IF NOT EXISTS vector;

-- ── Products ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS products (
    id               TEXT PRIMARY KEY,
    source           TEXT NOT NULL,
    source_record_id TEXT NOT NULL,
    title            TEXT NOT NULL,
    price            NUMERIC(10, 2) NOT NULL,
    condition        TEXT NOT NULL,
    category         TEXT NOT NULL,
    image_urls       TEXT[] NOT NULL DEFAULT '{}',
    size_raw         TEXT,
    size_eu          TEXT,
    brand            TEXT,
    color            TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Product embeddings (FashionSigLIP — 512 dims, L2-normalised) ─────────────
CREATE TABLE IF NOT EXISTS product_embeddings (
    id                SERIAL PRIMARY KEY,
    product_id        TEXT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    embedding         vector(512) NOT NULL,
    embedding_version TEXT NOT NULL DEFAULT 'fashionsiglip-v1',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- HNSW index — cosine distance. m=16 ef_construction=64 are pgvector defaults.
CREATE INDEX IF NOT EXISTS idx_product_embeddings_hnsw
    ON product_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- ── Interaction events — event log, source of truth for user preferences ─────
-- Schema mirrors contracts/events.py InteractionEvent.
CREATE TABLE IF NOT EXISTS interaction_events (
    event_id        UUID        PRIMARY KEY,
    user_id         UUID        NOT NULL,
    product_id      TEXT        NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    event_type      TEXT        NOT NULL,
    payload         JSONB       NOT NULL DEFAULT '{}',
    timestamp       TIMESTAMPTZ NOT NULL,
    schema_version  INTEGER     NOT NULL DEFAULT 1,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_interaction_events_user_time
    ON interaction_events (user_id, timestamp DESC);

-- ── User profiles ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id               UUID PRIMARY KEY,
    schema_version        INTEGER NOT NULL DEFAULT 1,
    hard_constraints      JSONB NOT NULL DEFAULT '{}',
    editable_preferences  JSONB NOT NULL DEFAULT '{}',
    vectors               JSONB NOT NULL DEFAULT '{}',
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
