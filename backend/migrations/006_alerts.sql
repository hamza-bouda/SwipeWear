-- KAN-69: Alert creation (specific item or style + constraints)
-- Gate 2 unlocked — free tier capped at 3 active alerts per user.

CREATE TABLE IF NOT EXISTS alerts (
    alert_id        UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID        NOT NULL,
    alert_type      TEXT        NOT NULL CHECK (alert_type IN ('specific_item', 'style')),
    label           TEXT        NOT NULL,
    reference_embedding JSONB   DEFAULT NULL,  -- 768-dim list[float] or null
    reference_product_id TEXT   DEFAULT NULL,
    constraints     JSONB       NOT NULL DEFAULT '{}',
    status          TEXT        NOT NULL DEFAULT 'active'
                                CHECK (status IN ('active', 'paused')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    schema_version  INTEGER     NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS alerts_user_status_idx
    ON alerts (user_id, status);
