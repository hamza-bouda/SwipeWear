-- Migration 003 — user_profiles.event_count (KAN-31)
--
-- contracts/profile.py::UserPreferenceProfile carries event_count, but
-- 001_init.sql's user_profiles table never got a column for it. Without
-- this, ProfileStore.save() followed by .load() cannot round-trip the
-- profile exactly (event_count would silently reset to 0 on every load).

ALTER TABLE user_profiles
    ADD COLUMN IF NOT EXISTS event_count INTEGER NOT NULL DEFAULT 0;
