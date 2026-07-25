-- Migration 014 — persist user accounts, and allow non-product events (KAN-88)
--
-- There was no users table at all: accounts, profiles and onboarding results
-- lived in Python dicts in api/store.py. Every restart or redeploy erased
-- every account, and with more than one replica two users could be served
-- from different memories. POST /events already wrote the profile to
-- user_profiles while GET /profile read the dict, so a swipe and the profile
-- screen disagreed by construction.
--
-- interaction_events.product_id also becomes nullable. The event log is the
-- source of truth (blueprint §3.6), but a preference edit is not about a
-- product: profile.py had to invent product_id="profile", which the foreign
-- key onto products rejects. NULL says "this event concerns no product"
-- honestly, instead of requiring a fake row to point at.

CREATE TABLE IF NOT EXISTS users (
    user_id       UUID PRIMARY KEY,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS users_email_idx ON users (email);

ALTER TABLE interaction_events
    ALTER COLUMN product_id DROP NOT NULL;
