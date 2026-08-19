-- First-party product analytics.  These events are deliberately separate
-- from interaction_events: they measure product usage but must not influence
-- the recommendation profile.

CREATE TABLE IF NOT EXISTS analytics_events (
    event_id    UUID PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    event_name  TEXT NOT NULL CHECK (char_length(event_name) BETWEEN 1 AND 80),
    properties  JSONB NOT NULL DEFAULT '{}',
    occurred_at TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_analytics_events_name_created
    ON analytics_events (event_name, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_analytics_events_user_created
    ON analytics_events (user_id, created_at DESC);
