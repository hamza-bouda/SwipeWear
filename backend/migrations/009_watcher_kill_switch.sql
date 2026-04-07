-- KAN-72: Kill switch for watcher sources (e.g. Vinted).
-- One row per watcher source; enabled=false hides products from the feed
-- and stops the watcher process, taking effect within the next request
-- (no redeploy required — checked at query time via watcher_sources join).
CREATE TABLE IF NOT EXISTS watcher_sources (
    source      TEXT        PRIMARY KEY,
    enabled     BOOLEAN     NOT NULL DEFAULT FALSE,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Vinted starts disabled; enable only after legal review (see watcher/LEGAL_REVIEW.md).
INSERT INTO watcher_sources (source, enabled)
VALUES ('vinted', false)
ON CONFLICT (source) DO NOTHING;
