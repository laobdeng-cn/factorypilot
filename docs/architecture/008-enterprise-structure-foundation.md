# Phase 1.1 — Enterprise Structure Foundation

## Scope

Phase 1.1 implements the first persistent enterprise-domain slice: Organization, Plant and Department. It intentionally does not add users, authentication, JWT, RBAC or audit yet; those remain Phase 1.2+ concerns.

## Model

- `Organization`: legal/operating company boundary and future top-level data-scope root.
- `Plant`: physical manufacturing site owned by an Organization.
- `Department`: enterprise department that belongs to an Organization and may optionally be scoped to a Plant or nested under another Department.

All three entities use UUID primary keys, stable business codes, active/inactive lifecycle, UTC timestamps and an optimistic-lock `version` field. Core enterprise entities are not physically deleted by the public API.

## Constraints

- Organization code is globally unique.
- Plant code is unique within an Organization.
- Department code is unique within an Organization.
- A Plant referenced by a Department must belong to the same Organization.
- A parent Department must belong to the same Organization.
- A Department cannot directly reference itself as parent.

## API

Phase 1.1 exposes typed `/api/v1` resources:

```text
GET/POST   /organizations
GET/PATCH  /organizations/{organization_id}
GET/POST   /plants
GET/PATCH  /plants/{plant_id}
GET/POST   /departments
GET/PATCH  /departments/{department_id}
```

Collections follow the Phase 0.8 pagination envelope. No DELETE endpoint is exposed; lifecycle changes use `is_active`.

## Migration

Alembic revision `20261008_0002` creates the three tables and foreign-key/index baseline on top of `20261008_0001`.

## Verification

Backend CI now provisions PostgreSQL with pgvector, applies `alembic upgrade head`, then runs the API integration test that creates an Organization → Plant → Department chain and verifies listing/update behavior.
