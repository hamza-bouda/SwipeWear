-- KAN-73: Premium subscription state (managed by RevenueCat webhook).
-- One row per user; upserted on each RevenueCat event.
-- is_premium() = status IN ('active','trialing','cancelled') AND (expires_at IS NULL OR expires_at > now())
CREATE TABLE IF NOT EXISTS user_subscriptions (
    user_id                 UUID        PRIMARY KEY,
    revenuecat_customer_id  TEXT,
    status                  TEXT        NOT NULL
        CHECK (status IN ('active', 'trialing', 'expired', 'refunded', 'cancelled')),
    expires_at              TIMESTAMPTZ,
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS user_subscriptions_status_idx
    ON user_subscriptions (status);
