-- Asset registry, processing jobs, artifacts and index records.
-- Each row keeps indexed scoping columns plus the full model as jsonb so the
-- API models can evolve without a migration per field.
CREATE TABLE IF NOT EXISTS assets (
    id text PRIMARY KEY,
    workspace_id text NOT NULL REFERENCES workspaces (id),
    tenant_id text NOT NULL REFERENCES tenants (id),
    status text NOT NULL,
    data jsonb NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS assets_workspace_idx ON assets (workspace_id);

CREATE TABLE IF NOT EXISTS asset_sources (
    id text PRIMARY KEY,
    asset_id text NOT NULL REFERENCES assets (id) ON DELETE CASCADE,
    data jsonb NOT NULL
);
CREATE INDEX IF NOT EXISTS asset_sources_asset_idx ON asset_sources (asset_id);

CREATE TABLE IF NOT EXISTS asset_uploads (
    id text PRIMARY KEY,
    asset_id text NOT NULL REFERENCES assets (id) ON DELETE CASCADE,
    data jsonb NOT NULL
);
CREATE INDEX IF NOT EXISTS asset_uploads_asset_idx ON asset_uploads (asset_id);

CREATE TABLE IF NOT EXISTS asset_versions (
    id text PRIMARY KEY,
    asset_id text NOT NULL REFERENCES assets (id) ON DELETE CASCADE,
    data jsonb NOT NULL
);
CREATE INDEX IF NOT EXISTS asset_versions_asset_idx ON asset_versions (asset_id);

CREATE TABLE IF NOT EXISTS processing_jobs (
    id text PRIMARY KEY,
    asset_id text NOT NULL REFERENCES assets (id) ON DELETE CASCADE,
    workspace_id text NOT NULL,
    status text NOT NULL,
    data jsonb NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS processing_jobs_asset_idx ON processing_jobs (asset_id);
CREATE INDEX IF NOT EXISTS processing_jobs_status_idx ON processing_jobs (status);

CREATE TABLE IF NOT EXISTS artifacts (
    id text PRIMARY KEY,
    asset_id text NOT NULL REFERENCES assets (id) ON DELETE CASCADE,
    workspace_id text NOT NULL,
    artifact_type text NOT NULL,
    data jsonb NOT NULL
);
CREATE INDEX IF NOT EXISTS artifacts_asset_idx ON artifacts (asset_id);
CREATE INDEX IF NOT EXISTS artifacts_workspace_idx ON artifacts (workspace_id);

CREATE TABLE IF NOT EXISTS index_records (
    id text PRIMARY KEY,
    asset_id text NOT NULL REFERENCES assets (id) ON DELETE CASCADE,
    workspace_id text NOT NULL,
    index_type text NOT NULL,
    status text NOT NULL,
    data jsonb NOT NULL
);
CREATE INDEX IF NOT EXISTS index_records_asset_idx ON index_records (asset_id);
