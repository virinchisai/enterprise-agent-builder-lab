# Operations and handover

## Security and reliability
Trust the API authorization layer rather than prompts. Entra mode validates RS256 signature against tenant JWKS, issuer, audience, expiry, tenant, object ID, v2 token and delegated scope. Reviewer role is checked on the server. Local tests only exercise missing Entra configuration; validate actual token acceptance and negative cases in a real test tenant. JWKS failures deny access. No external token introspection or continuous access evaluation is implemented.

Tickets are owned by authenticated subject. Idempotency is scoped by owner; a transaction serializes duplicate requests and checks a canonical body hash. Access tickets remain pending until a distinct reviewer approves. Approval record binds ticket, owner and body hash via HMAC, expires after 30 minutes and is single-use under a SQLite write transaction. Review and approval only change synthetic ticket state. Audit stores actor/action/target/time, not payloads. Reviewer role is tenant-wide for this single-tenant lab. No production retention, audit tamper protection, multi-tenant partitioning or role review automation is implemented.

## Deploy
Run local tests and smoke test before deployment. Docker defaults to nonroot process; Compose binds loopback. A hosted instance requires separate Entra configuration, HTTPS, controlled ingress, resource limits, secret management, logging restrictions, secure backups and an approved host. Use a durable volume, single worker, and separate environments. SQLite is appropriate for this demo, not a multi-replica production deployment. For scale, migrate to PostgreSQL, add migrations, connection pooling, distributed rate limiting, telemetry and durable jobs. Add malware/content inspection for real documents. No public deployment has been performed.

## Monitor and recover
Health endpoint confirms process responsiveness. Reviewer-only metrics reports counts; logs emit event and target. Add latency/error counters, tracing and alerts in a real environment. Do not log access tokens or ticket summaries. For ambiguous write failure, reuse the original idempotency key. If approval response was lost, read approval/ticket status before acting. Back up SQLite with its backup API while running or stop service and preserve database state; validate restoration into a separate instance. Preserve signing secret across restore. For rollback, disable agent tools, restore previous tested application version and compatible data snapshot after impact review; do not blindly roll back data if new writes occurred.

## Handover checklist
Document owner, environment IDs, API URLs, app registration IDs (not secrets), scopes and roles, connector operation schemas, agent instructions, flow input/output mapping, known limits, backup/restore, escalation contacts and acceptance evidence. Record actual Power Platform test results before claiming deployed integration. Include security review and rollback approval.
