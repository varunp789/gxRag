-- Usage metering and the append-only audit log.
CREATE TABLE IF NOT EXISTS usage_counters (
    workspace_id text NOT NULL,
    period text NOT NULL,           -- YYYY-MM, so quotas reset monthly
    unit text NOT NULL,
    quantity bigint NOT NULL DEFAULT 0,
    PRIMARY KEY (workspace_id, period, unit)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id bigserial PRIMARY KEY,
    actor text NOT NULL,
    action text NOT NULL,
    resource_type text NOT NULL,
    resource_id text NOT NULL,
    workspace_id text,
    occurred_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS audit_logs_workspace_idx ON audit_logs (workspace_id, occurred_at DESC);

-- Audit rows are append-only: block UPDATE and DELETE at the database level.
CREATE OR REPLACE FUNCTION audit_logs_immutable() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'audit_logs is append-only';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS audit_logs_no_update ON audit_logs;
CREATE TRIGGER audit_logs_no_update BEFORE UPDATE OR DELETE ON audit_logs
    FOR EACH ROW EXECUTE FUNCTION audit_logs_immutable();
