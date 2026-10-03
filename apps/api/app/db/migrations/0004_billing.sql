-- Stripe customer mapping (one customer per tenant) and webhook replay protection.
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS stripe_customer_id text UNIQUE;

CREATE TABLE IF NOT EXISTS webhook_events (
    provider text NOT NULL,
    event_id text NOT NULL,
    received_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (provider, event_id)
);
