# Incident response runbook

1. Acknowledge the incident and record the time, affected workspaces, and incident owner.
2. Inspect `/v1/admin/health`, queue backlog, index diagnostics, and failed jobs.
3. Pause unsafe ingest sources, retry a single failed job, and use the dead-letter record for repeat failures.
4. Preserve audit logs and source evidence. Do not delete customer data during investigation.
5. Communicate impact, mitigation, and recovery; complete a post-incident review with corrective actions.
