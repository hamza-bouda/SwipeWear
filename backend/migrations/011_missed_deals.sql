-- KAN-74: "Pépites manquées" — products that sold out during the free-tier 30-min delay.
-- Recorded when flush_due_notifications() finds a pending notification for an unavailable product.
-- Shown in the alerts screen as a conversion argument ("You missed N deals — go Premium").
CREATE TABLE IF NOT EXISTS missed_deals (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID        NOT NULL,
    alert_id    UUID        NOT NULL,
    product_id  TEXT        NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS missed_deals_user_idx ON missed_deals (user_id);
CREATE INDEX IF NOT EXISTS missed_deals_user_alert_idx ON missed_deals (user_id, alert_id);
