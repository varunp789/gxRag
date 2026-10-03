-- Access layer: tenants, workspaces, users, memberships, API keys, plans.
CREATE TABLE IF NOT EXISTS plans (
    id text PRIMARY KEY,
    name text NOT NULL,
    monthly_document_limit integer NOT NULL,
    monthly_query_limit integer NOT NULL,
    max_workspace_members integer NOT NULL
);

CREATE TABLE IF NOT EXISTS tenants (
    id text PRIMARY KEY,
    name text NOT NULL,
    slug text NOT NULL UNIQUE,
    plan_id text NOT NULL REFERENCES plans (id),
    status text NOT NULL
);

CREATE TABLE IF NOT EXISTS workspaces (
    id text PRIMARY KEY,
    tenant_id text NOT NULL REFERENCES tenants (id),
    name text NOT NULL,
    slug text NOT NULL UNIQUE,
    environment text NOT NULL,
    region text NOT NULL,
    status text NOT NULL
);
CREATE INDEX IF NOT EXISTS workspaces_tenant_idx ON workspaces (tenant_id);

CREATE TABLE IF NOT EXISTS users (
    id text PRIMARY KEY,
    email text NOT NULL UNIQUE,
    full_name text NOT NULL
);

CREATE TABLE IF NOT EXISTS admin_users (
    id text PRIMARY KEY,
    email text NOT NULL UNIQUE,
    full_name text NOT NULL,
    roles text[] NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS workspace_members (
    id text PRIMARY KEY,
    workspace_id text NOT NULL REFERENCES workspaces (id) ON DELETE CASCADE,
    user_id text NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    role text NOT NULL,
    status text NOT NULL,
    UNIQUE (workspace_id, user_id)
);

CREATE TABLE IF NOT EXISTS api_keys (
    id text PRIMARY KEY,
    workspace_id text NOT NULL REFERENCES workspaces (id) ON DELETE CASCADE,
    name text NOT NULL,
    prefix text NOT NULL UNIQUE,
    key_hash text,
    role text NOT NULL,
    status text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    revoked_at timestamptz
);
CREATE INDEX IF NOT EXISTS api_keys_workspace_idx ON api_keys (workspace_id);
