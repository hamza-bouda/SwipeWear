-- Migration 017 — accounts come from an external identity provider (KAN-90)
--
-- Supabase now owns credentials, OAuth with Google and Apple, password resets
-- and email confirmation. The backend stores no password at all, so
-- password_hash becomes nullable rather than being dropped: rows created
-- before this change keep their hash until those accounts are re-linked, and
-- removing the column would destroy the only record of how they were made.
--
-- email becomes nullable too. It is NOT NULL today because our own signup form
-- demanded one, but an external provider does not guarantee it — Sign in with
-- Apple can withhold the address, and an anonymous Supabase session has none.
-- A UNIQUE constraint tolerates several NULLs in Postgres, so uniqueness of
-- real addresses is preserved.
--
-- user_id is unchanged and still the primary key: Supabase's `sub` claim is a
-- UUID and is stored directly. A second identifier plus a mapping table would
-- be two ways to name the same person, and therefore a way for them to
-- disagree.

ALTER TABLE users
    ALTER COLUMN password_hash DROP NOT NULL;

ALTER TABLE users
    ALTER COLUMN email DROP NOT NULL;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS auth_provider TEXT NOT NULL DEFAULT 'password';

-- Which provider actually signed the user in (email, google, apple, …).
-- Kept because "delete my account" has to reach the right place, and because
-- an Apple relay address behaves differently from one the user typed.
COMMENT ON COLUMN users.auth_provider IS
    'Identity provider that authenticated this account: password (legacy, local), email, google, apple, …';
