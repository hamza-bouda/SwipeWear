-- Migration 018 — global notification preferences
--
-- alert_notification_prefs is intentionally per-alert (user_id + alert_id +
-- frequency). The profile screen also needs one global preference for the
-- device/account, so it must live in its own table rather than mixing the two
-- scopes or relying on a non-existent `preference` column.

CREATE TABLE IF NOT EXISTS notification_preferences (
    user_id     UUID PRIMARY KEY,
    preference  TEXT NOT NULL DEFAULT 'instant'
                CHECK (preference IN ('instant', 'daily_digest', 'disabled')),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
