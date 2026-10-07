# Phase 1.3 — JWT Access / Refresh Token + Session Revocation

## Scope

Phase 1.3 upgrades FactoryPilot from password verification to revocable authenticated sessions.

Implemented boundaries:

- short-lived JWT access tokens;
- rotating JWT refresh tokens;
- server-side `auth_sessions` persistence;
- immediate session revocation;
- `GET /api/v1/auth/me` current-user context;
- logout of the current session;
- password changes and account deactivation revoke existing sessions.

RBAC and permission evaluation remain Phase 1.4 concerns.

## Token Model

Access tokens are signed JWTs with a 15-minute default lifetime. They carry:

- `sub`: user ID;
- `sid`: authentication session ID;
- `jti`: token ID;
- `typ=access`;
- `org`: organization ID;
- `dept`: department ID when present;
- `plant`: primary plant ID when present;
- standard `iat`, `exp`, `iss`, and `aud` claims.

Refresh tokens are signed JWTs with a seven-day default lifetime. The database never stores the raw refresh token. Only its SHA-256 digest is stored in `auth_sessions.refresh_token_hash`.

## Refresh Rotation

`POST /api/v1/auth/refresh` verifies the JWT and the persisted digest. A successful refresh rotates the refresh token while preserving the same session ID. Reuse of an older rotated token revokes the entire session with reason `refresh_token_reuse`.

This gives FactoryPilot a server-side kill switch even though access and refresh credentials are JWTs.

## Session Revocation

An access token is accepted only when its referenced `auth_sessions` row exists and is active. Therefore session revocation takes effect immediately rather than waiting for access-token expiry.

Current revocation sources:

- explicit logout;
- password change/reset;
- user account deactivation;
- refresh-token reuse detection.

## Current User Context

The `CurrentUser` dependency resolves the access token into the current database-backed identity context:

- `user_id`;
- `session_id`;
- `organization_id`;
- `department_id`;
- `primary_plant_id`;
- current `User` entity.

Phase 1.4 RBAC will build permission and data-scope evaluation on this context instead of trusting client-provided organization or plant identifiers.

## Security Configuration

Development defaults exist only to keep the local stack bootable. Non-development deployments must provide a high-entropy `FACTORYPILOT_JWT_SECRET_KEY` through deployment secrets and must never reuse the documented development secret.

Default timings:

- access token: 15 minutes;
- refresh session: 7 days.

These are configurable with `FACTORYPILOT_ACCESS_TOKEN_MINUTES` and `FACTORYPILOT_REFRESH_TOKEN_DAYS`.

## API Surface

```text
POST /api/v1/auth/login
POST /api/v1/auth/refresh
GET  /api/v1/auth/me
POST /api/v1/auth/logout
```

`Authorization: Bearer <access_token>` is required for `/auth/me` and `/auth/logout`.
