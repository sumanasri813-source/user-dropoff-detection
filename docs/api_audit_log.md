# Audit Log API

This document describes the audit-log API endpoints.

Endpoints

- GET /admin/audit-logs?page=1&per_page=50
  - Description: Paginated view of audit logs. Admin only.
  - Auth: Bearer token with `admin` role or valid X-API-Key
  - Response: { page, per_page, total, logs: [{id,user_id,action,resource_type,resource_id,changes_summary,created_at}, ...] }

- DELETE /admin/audit-logs/{id}
  - Description: Delete an audit-log entry.
  - Auth: Admin only (Bearer token role=admin)
  - Body: { "reason": "explain why this entry is removed" } (min 5 chars)
  - Response: { deleted: true, log_id: <id> }

Retention

- The system runs cleanup during the monitoring cycle. Set `AUDIT_RETENTION_DAYS` (env) to control retention. Default: 90 days.

Security notes

- Deleting audit logs requires an admin token and a non-empty reason; deletion itself is recorded in the audit logs.
