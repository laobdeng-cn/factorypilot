# Phase 1.2 — User + Password Authentication

## Scope

Phase 1.2 establishes the FactoryPilot human user account and password-verification foundation. It deliberately does **not** issue JWT access or refresh tokens; token/session semantics are Phase 1.3.

## User model

`users` stores enterprise identity facts:

- UUID primary key
- `organization_id`
- optional `department_id`
- optional `primary_plant_id`
- globally unique normalized `username`
- organization-scoped `employee_no`
- display name, email and mobile
- Argon2id `password_hash`
- active state
- failed-login counter and temporary lock timestamp
- last successful login timestamp
- optimistic-lock `version`
- UTC creation/update timestamps

Password plaintext is accepted only at write boundaries and is never returned by API responses or stored in logs/database columns.

## Password policy

FactoryPilot uses Argon2id through `argon2-cffi` with explicit memory/time/parallelism parameters. Passwords must be 12–128 characters and include lowercase, uppercase, number and special-character classes, with no whitespace.

Five consecutive invalid password attempts trigger a 15-minute account lock. A successful login resets the failure state. Unknown usernames execute a dummy Argon2 verification to reduce timing differences.

## API baseline

```text
GET    /api/v1/users
POST   /api/v1/users
GET    /api/v1/users/{user_id}
PATCH  /api/v1/users/{user_id}
POST   /api/v1/users/{user_id}/password
POST   /api/v1/auth/login
```

`POST /auth/login` only validates credentials and updates login security metadata in Phase 1.2. It does not establish an authenticated browser/API session yet.

## Phase boundary

These endpoints are development foundations until Phase 1.3/1.4 adds bearer-token/session authentication and RBAC. Production authorization must never rely on the current unauthenticated management routes.
