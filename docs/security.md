# Security model

## Authentication

| Mode | `GXRAG_AUTH_MODE` | Identity source |
|---|---|---|
| Development | `dev` | `X-Actor-Email` / `X-Admin-Email` headers. **Local use only** - anyone can claim any identity. |
| Production | `jwt` | `Authorization: Bearer <token>` |

The API refuses to start when `GXRAG_ENVIRONMENT` is anything other than `development` unless
`GXRAG_AUTH_MODE=jwt`, `GXRAG_JWT_SECRET` is at least 32 characters, and `GXRAG_DATABASE_URL` is set
(`Settings.validate_for_runtime`). OpenAPI docs are served only in development.

Bearer credentials in `jwt` mode:

* **User / admin token** - HS256 JWT with `sub`, `email`, `iss` (= `GXRAG_JWT_ISSUER`), `exp`, and `typ`
  (`user` or `admin`). The algorithm is pinned (`alg: none` and other algorithms are rejected), expiry and issuer
  are enforced, and the email must exist in the catalog. Tokens are signed with the shared
  `GXRAG_JWT_SECRET`; mint operator tokens with `python -m app.core.security <email> [admin]`.
* **Workspace API key** - `gxk_<prefix>_<secret>`. Only a SHA-256 of the secret is stored, the full key is
  returned once at creation, comparison is constant-time, and a key is bound to a single workspace (an
  `X-Workspace-Id` for another workspace is refused). Keys can hold only `ingestion_writer` or
  `retrieval_reader`; revocation takes effect immediately.

> **Open item - external IdP.** Verification today uses a shared HMAC secret. Integrating an OIDC provider
> (RS256 + JWKS rotation) is not implemented and is the remaining piece of "production authentication
> provider" in `PHASE_CHECKLIST.md`.

## Authorisation (RBAC)

Every route declares the permission it needs (`require_permission` for workspace routes, `require_admin` for
operator routes). A user's role comes from their **active** membership in the target workspace; invited or
missing memberships are denied. Admin routes never accept user or API-key credentials.

| Permission | workspace_owner | analyst | ingestion_writer | retrieval_reader | support_admin | platform_admin |
|---|---|---|---|---|---|---|
| `workspace.read` | ✓ | ✓ |  |  |  |  |
| `assets.read` | ✓ | ✓ | ✓ | ✓ |  |  |
| `assets.write` | ✓ |  | ✓ |  |  |  |
| `assets.delete` | ✓ |  |  |  |  |  |
| `assets.export` | ✓ |  |  |  |  |  |
| `query.run` | ✓ | ✓ |  | ✓ |  |  |
| `usage.read` | ✓ | ✓ |  |  |  |  |
| `api_key.manage` | ✓ |  |  |  |  |  |
| `billing.manage` | ✓ |  |  |  |  |  |
| `admin.support` |  |  |  |  | ✓ | ✓ |
| `admin.operate` |  |  |  |  |  | ✓ |
| `audit.read` |  |  |  |  |  | ✓ |

## Tenant isolation

Every asset, artifact, job, index record, usage counter and audit row carries `workspace_id`. Service
functions filter on the authenticated workspace and return `404` (not `403`) for foreign resource ids.
`tests/test_isolation.py` covers asset reads, graph/entity/relation reads, export, delete, process, queries in
every mode, hosted answers, usage, audit scoping and workspace selection across two tenants. Retrieval
reads only artifacts under `<artifact_root>/<workspace_id>/<asset_id>/`.

## Audit

Audit rows (`audit_logs`) record the authenticated actor, action, resource and workspace. The table is
append-only: a database trigger rejects `UPDATE` and `DELETE`. Workspace owners read their own trail at
`GET /v1/audit-logs`; platform admins read all at `GET /v1/admin/audit-logs` (`audit.read`).

## Webhooks and billing

* Signature format (Stripe-compatible): `t=<unix>,v1=<hex>` where `v1 = HMAC_SHA256(secret, "<t>.<body>")`.
  Header `X-Gxrag-Signature` (secret `GXRAG_WEBHOOK_SECRET`) or `Stripe-Signature` for `/webhooks/stripe`
  (secret `GXRAG_STRIPE_WEBHOOK_SECRET`). Timestamps older than 5 minutes are rejected and event ids are
  de-duplicated, so captured requests cannot be replayed. With no secret configured, webhooks fail closed.
* The billing portal opens the Stripe customer **linked to the caller's tenant** by an operator
  (`PUT /v1/admin/tenants/{id}/billing-customer`); a client-supplied customer id is never accepted, and
  `return_url` must match `GXRAG_BILLING_RETURN_ORIGINS`.

## Abuse controls

Per-credential rate limiting (`GXRAG_RATE_LIMIT_PER_MINUTE`, bounded memory), monthly document/query quotas
per plan, and request tracing (`X-Trace-Id`, capped at 64 characters).

## Known limitations

* Rate limits are per API process; run a shared limiter (Redis) before scaling the API horizontally.
* Query and hosted-answer logs (`/admin/query-logs`, `/admin/answer-logs`) and the answer cache are in
  process memory, not durable.
* The tenant/workspace/user catalog is seeded from code (`migrate --seed`); there is no self-service
  tenant, user or membership management API yet.
* Secrets scanning, `pip-audit` and `npm audit` run in CI (`.github/workflows/ci.yml`).
* PII handling, retention and access-review **policies** need human approval; this repo only provides the
  mechanisms (retention purge, append-only audit, scoped export).
