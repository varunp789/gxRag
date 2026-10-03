# Governance controls

The API applies request rate limits, plan-based document/query quotas, and workspace usage metering. Asset export is workspace-scoped. Deletion requests are recorded, set the asset to `deleted`, redact its source and stop it being retrievable. The retention job (`python -m app.services.retention`, `GXRAG_RETENTION_DAYS`) then permanently removes artifacts, index entries and registry rows.

Webhook endpoints require a timestamped HMAC-SHA256 signature (`t=<unix>,v1=<hex>` over `<t>.<body>`), reject timestamps older than 5 minutes and de-duplicate event ids; see `docs/security.md`. Keep all secrets in the deployment secret manager, never in source control. Do not upload unnecessary personal data; source data, derived artifacts, citations, and audit records must follow the customer’s retention policy.

Set `GXRAG_STRIPE_SECRET_KEY` and link each tenant to its Stripe customer (`PUT /v1/admin/tenants/{id}/billing-customer`) to enable `POST /v1/billing/portal`, which creates a billing-portal session for the caller's own tenant. Usage events are the source of billable documents, retrieval queries, and hosted tokens.
