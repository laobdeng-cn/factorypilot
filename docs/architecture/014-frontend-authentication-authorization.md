# Phase 1.7 — Frontend Authentication + Permission-aware Navigation

## Scope

Phase 1.7 connects the existing Umi Max / Ant Design Pro frontend to the Phase 1 identity and authorization backend.

Implemented boundaries:

- dedicated `/login` page outside the application layout;
- login against `POST /api/v1/auth/login`;
- persisted access / refresh token pair for the local web client;
- proactive access-token rotation near expiry;
- one retry after a `401` using `POST /api/v1/auth/refresh`;
- current-user bootstrap from `GET /api/v1/auth/me`;
- explicit logout through `POST /api/v1/auth/logout`;
- Umi `initialState` as the frontend current-user source of truth;
- Umi access plugin for authenticated routes and permission-aware system menus;
- redirect to `/login?redirect=...` when an unauthenticated user reaches the application shell.

This phase does not move authorization authority to the browser. FastAPI RBAC and Data Scope checks remain authoritative for every protected backend operation.

## Frontend Session Model

The browser stores a compact session record under `factorypilot.auth.session.v1` containing:

- access token;
- refresh token;
- calculated access-token expiry timestamp;
- calculated refresh-token expiry timestamp.

The frontend begins rotation 30 seconds before access-token expiry. Refresh rotation replaces both stored tokens with the latest pair returned by the server. A failed or expired refresh clears the local session.

The backend continues to enforce the persisted `auth_sessions` record, so server-side revocation takes effect even if the browser still contains a JWT.

> Production hardening may replace local storage with an HttpOnly same-site cookie/BFF strategy. Phase 1.7 intentionally follows the current JSON token contract so the existing backend can be integrated without changing the Phase 1.3 API surface.

## Current User Context

`src/app.tsx#getInitialState` resolves the authenticated context with `/api/v1/auth/me`.

The frontend state includes:

- identity and organization identifiers;
- current role codes;
- current permission codes;
- effective Data Scope type and source;
- the current `UserRead` payload.

The navigation layer consumes this state through `src/access.ts`.

## Access Policy

All business routes require `authenticated`.

The current system-management menu has additional visibility rules:

| Route | Frontend access capability |
| --- | --- |
| `/system/health` | authenticated |
| `/system/organization` | enterprise read capability |
| `/system/rbac` | RBAC read capability |
| `/system/integrations` | authenticated |
| `/system/audit` | audit read capability |

Menu visibility is UX only. A hidden menu item is not treated as a security boundary.

## Authenticated Request Contract

New protected frontend services should call `apiFetch` from `src/services/auth.ts` rather than creating their own Bearer-token logic.

`apiFetch`:

1. loads the active token pair;
2. rotates the access token when it is close to expiry;
3. adds `Authorization: Bearer <access_token>`;
4. retries once after a `401` when refresh succeeds.

This keeps token rotation in one place and avoids multiple feature modules implementing inconsistent session behavior.

## Local Acceptance

Run the backend on port `8000` and the web app on port `8001`, then verify:

1. opening `/dashboard` without a stored session redirects to `/login`;
2. `admin.fp` can sign in and returns to `/dashboard`;
3. the header displays the current user's display name;
4. logout revokes the server session and returns to `/login`;
5. a `viewer` account can enter normal authenticated pages but does not see RBAC or audit menu entries without the corresponding permissions;
6. refreshing the browser restores the user context through `/api/v1/auth/me`;
7. web quality checks pass:

```bash
pnpm --dir apps/web lint
pnpm --dir apps/web typecheck
pnpm --dir apps/web test
pnpm --dir apps/web build
```
