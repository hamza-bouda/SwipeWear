-- KAN-71: Push notifications infrastructure
-- Tables: device_tokens, notification_queue, notification_log

-- Device tokens per user/device (Expo push tokens)
CREATE TABLE IF NOT EXISTS device_tokens (
    token_id        UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID        NOT NULL,
    expo_token      TEXT        NOT NULL,
    platform        TEXT        NOT NULL CHECK (platform IN ('ios', 'android', 'unknown')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, expo_token)
);

CREATE INDEX IF NOT EXISTS device_tokens_user_idx ON device_tokens (user_id);

-- Per-alert notification preferences
CREATE TABLE IF NOT EXISTS alert_notification_prefs (
    user_id     UUID    NOT NULL,
    alert_id    UUID    NOT NULL REFERENCES alerts (alert_id) ON DELETE CASCADE,
    frequency   TEXT    NOT NULL DEFAULT 'instant'
                        CHECK (frequency IN ('instant', 'daily_digest', 'disabled')),
    PRIMARY KEY (user_id, alert_id)
);

-- Notification queue (scheduled sends, supports 30-min delay for free users)
CREATE TABLE IF NOT EXISTS notification_queue (
    queue_id        UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID        NOT NULL,
    alert_id        UUID        REFERENCES alerts (alert_id) ON DELETE CASCADE,
    product_id      TEXT        NOT NULL,
    match_tier      TEXT        NOT NULL CHECK (match_tier IN ('exact', 'similar')),
    product_price   FLOAT       DEFAULT NULL,
    product_image   TEXT        DEFAULT NULL,
    is_digest       BOOLEAN     NOT NULL DEFAULT FALSE,
    scheduled_for   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sent_at         TIMESTAMPTZ DEFAULT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS notification_queue_pending_idx
    ON notification_queue (scheduled_for)
    WHERE sent_at IS NULL;

CREATE INDEX IF NOT EXISTS notification_queue_user_date_idx
    ON notification_queue (user_id, created_at);

-- Notification log (sent + opened tracking for metrics)
CREATE TABLE IF NOT EXISTS notification_log (
    log_id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    queue_id        UUID        REFERENCES notification_queue (queue_id),
    user_id         UUID        NOT NULL,
    expo_token      TEXT        NOT NULL,
    sent_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    opened_at       TIMESTAMPTZ DEFAULT NULL,
    expo_status     TEXT        DEFAULT NULL
);

CREATE INDEX IF NOT EXISTS notification_log_user_idx ON notification_log (user_id);
