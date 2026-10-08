# Phase 1.6 — Audit Log / Security Event / Authorization Audit

## Goal

Phase 1.6 introduces an append-only audit foundation for FactoryPilot. The design separates routine operation audit records from security events while preserving the request and authorization context required for incident review.

## Data model

### `audit_logs`

Each API operation records:

- actor user and authentication session
- organization boundary
- action and resource type / resource id
- result (`success`, `denied`, `error`)
- denial/error reason
- required permission code when RBAC was evaluated
- effective data-scope type
- request id, source IP and user agent
- request metadata such as method, route, query and status code
- immutable occurrence timestamp

### `security_events`

Security events are emitted for authentication, authorization and session lifecycle activity, including:

- login success and failure
- account locked / inactive decisions
- refresh success and refresh-token reuse failures
- logout and explicit session revocation
- HTTP 401 / 403 / 423 authorization failures

Both tables are append-only. PostgreSQL triggers reject `UPDATE` and `DELETE` so audit history cannot be silently rewritten by application code.

## Request pipeline

The HTTP middleware owns audit persistence. Authentication attaches actor/session/organization/data-scope context to `request.state`; permission dependencies attach the required permission and authorization result; exception handlers attach structured error codes. After the response is produced, the middleware writes the final immutable audit record using an independent database session.

Audit persistence is fail-open for the business request: if the audit database write fails, the application logs `audit_persist_failed` but does not replace a successful business response with a secondary audit failure. Infrastructure alerting must treat this log as a security/operations fault.

## RBAC

Phase 1.6 seeds three permissions for the system administrator role:

- `audit.log.read`
- `audit.security_event.read`
- `audit.authorization.read`

Audit records themselves have no update/delete API.

## Query API

- `GET /api/v1/audit/logs`
- `GET /api/v1/audit/authorization`
- `GET /api/v1/audit/security-events`

All endpoints are paginated and support actor/time/result/category-specific filters. Non-global callers are restricted to their organization boundary even if an audit-read permission is later delegated to another role.

## Security constraints

- Access and refresh tokens are never stored in audit metadata.
- Request bodies are not captured by the generic middleware.
- Failed login audit metadata stores only the normalized username subject, never the password.
- Client IP honors the first `X-Forwarded-For` value when present; production reverse proxies must sanitize that header.
- Audit table mutations are rejected at the database layer.
