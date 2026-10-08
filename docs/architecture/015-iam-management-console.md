# Phase 1.8 — IAM Management Console

Phase 1.8 exposes the identity and authorization foundation completed in Phase 1.1–1.7 as an operator-facing administration console.

## Pages

- `/system/organization` — Organization / Plant / Department hierarchy, create and edit flows.
- `/system/users` — user lifecycle, organization placement, role assignment, password reset and user Data Scope override.
- `/system/rbac` — role lifecycle, permission assignment and role default Data Scope.
- `/system/data-scope` — role defaults, user overrides and effective scope inspection.

## Authorization model

Frontend route and action visibility is driven by `permission_codes` returned by `/api/v1/auth/me`.

The frontend is not an authorization boundary. Every mutation and query is still enforced by FastAPI `require_permission(...)` dependencies and hierarchical Data Scope filtering.

Relevant frontend access flags:

- `canReadEnterprise` / `canManageEnterprise`
- `canReadUsers` / `canManageUsers`
- `canReadRbac` / `canManageRbac`
- `canReadUserRoles` / `canManageUserRoles`
- `canReadDataScope` / `canManageDataScope`
- `canReadAudit`

## API integration

`apps/web/src/services/iam.ts` centralizes Phase 1 administration requests and reuses the Phase 1.7 authenticated `apiFetch` layer, including access-token refresh and retry behavior.

Covered API groups:

- `/api/v1/organizations`, `/plants`, `/departments`
- `/api/v1/users`
- `/api/v1/roles`, `/permissions`
- `/api/v1/users/{id}/roles`
- `/api/v1/roles/{id}/data-scope`
- `/api/v1/users/{id}/data-scope`

## Acceptance targets

1. `system_admin` can open all four administration pages and perform permitted mutations.
2. a read-only `viewer` sees only routes supported by its permission codes and cannot invoke hidden management actions from the UI.
3. organization, plant and department lists remain filtered by backend Data Scope.
4. role permission changes are reflected after refresh.
5. role Data Scope and user override changes are reflected by `/api/v1/auth/me` after the affected user signs in again.
6. 401 responses continue through the shared refresh-token flow; 403 responses are surfaced as API errors without bypassing backend policy.
