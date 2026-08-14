# Governance controls

The API applies request rate limits, plan-based document/query quotas, and workspace usage metering. Asset export is workspace-scoped. Deletion requests are recorded and set an asset to `deleted`; a production retention worker should permanently remove the underlying object at the configured retention deadline.

Webhook endpoints require an `X-Gxrag-Signature` HMAC-SHA256 using `GXRAG_WEBHOOK_SECRET`. Keep all secrets in the deployment secret manager, never in source control. Do not upload unnecessary personal data; source data, derived artifacts, citations, and audit records must follow the customer’s retention policy.

Set `GXRAG_STRIPE_SECRET_KEY` to enable `POST /v1/billing/portal`, which creates a Stripe customer billing-portal session. Usage events are the source of billable documents, retrieval queries, and hosted tokens.
