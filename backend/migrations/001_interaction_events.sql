-- KAN-18: interaction_events table
-- Event log is the source of truth: profiles are rebuilt by replaying rows.

CREATE TABLE IF NOT EXISTS interaction_events (
    event_id        UUID        PRIMARY KEY,
    user_id         UUID        NOT NULL,
    product_id      TEXT        NOT NULL,
    event_type      TEXT        NOT NULL,
    payload         JSONB       NOT NULL DEFAULT '{}',
    timestamp       TIMESTAMPTZ NOT NULL,
    schema_version  INTEGER     NOT NULL DEFAULT 1,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Primary query: all events for a user ordered by time (profile replay)
CREATE INDEX IF NOT EXISTS idx_interaction_events_user_timestamp
    ON interaction_events (user_id, timestamp);
