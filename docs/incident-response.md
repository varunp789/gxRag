# Incident response runbook

1. Acknowledge the incident and record the time, affected workspaces, and incident owner.
2. Inspect `/v1/admin/health`, queue backlog, index diagnostics, and failed jobs.
3. Pause unsafe ingest sources, retry a single failed job, and use the dead-letter record for repeat failures.
4. Preserve audit logs and source evidence. Do not delete customer data during investigation.
5. Communicate impact, mitigation, and recovery; complete a post-incident review with corrective actions.

## Triage reference

| Symptom | Check | Action |
|---|---|---|
| `/v1/ready` 503 | `checks` in the body (database / queue) | Restore the dependency; API recovers without restart. |
| `dead_letter` > 0 | `GET /v1/admin/jobs` (status `failed`) | Read step warnings; fix cause; `POST /v1/admin/jobs/{id}/retry`. |
| Jobs `completed_with_index_errors` | `GET /v1/admin/index/diagnostics` | Restore OpenSearch/ArangoDB/pgvector, then `POST /v1/admin/index/reconcile`. |
| Suspected cross-tenant exposure | `GET /v1/admin/audit-logs` | Revoke affected API keys, rotate `GXRAG_JWT_SECRET`, preserve logs. |
| Leaked API key | owner revokes via `DELETE /v1/api-keys/{id}` | Effective immediately; review the audit trail for the key's actions. |
| Retention failures | `retention.purge_failed` log events | Fix backend access; the next run retries. |
