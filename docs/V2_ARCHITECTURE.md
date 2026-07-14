# Dhan Trading Platform — Version 2 Architecture

## Architecture Strategy

Version 2 preserves the Version 1 backend and adds a new interactive product
surface incrementally. Stable repositories, services, migrations and `/api/v1`
remain authoritative and are not redesigned for architectural purity.

```text
Browser workspace
       │
       │ versioned HTTP application APIs
       ▼
Version 2 application boundary
       │
       ├── read query services ── repositories ── PostgreSQL
       ├── authenticated commands ── existing domain services
       └── Copilot service ── verified application evidence

Existing pipelines ── Dhan APIs
Existing alert adapters ── approved private destinations
```

The browser never connects to PostgreSQL, Redis, Dhan, model providers, alert
destinations or broker services directly.

## Preserved Version 1 Foundations

- PostgreSQL remains the system of record.
- Repositories remain the only database-access layer.
- Services retain deterministic business policy.
- `ExpiryService` remains the exclusive expiry-selection policy owner.
- Analytics, ranking, selection, risk and signals retain exact persisted lineage.
- Replay and backtesting continue to use persisted data only.
- Paper state remains stored separately and cannot become executable intent.
- Copilot evidence remains application-selected and provider-isolated.
- Existing production equity and option pipelines remain separate and compatible.
- Migrations `001`–`017` remain immutable.

## API Compatibility Policy

`/api/v1` remains stable, GET-only and backward compatible. Existing dashboard and
Copilot consumers must continue to pass unchanged contract tests.

Version 2 may add purpose-built `/api/v2` read projections as product workspaces
need them. Additions must:

- use thin HTTP handlers;
- validate filters and bounded pagination explicitly;
- call query services or repositories rather than embed business policy;
- expose freshness and lineage identifiers;
- never trigger collection, calculations or Dhan calls;
- avoid changing `/api/v1` response semantics.

The standard-library WSGI API remains the approved starting point. FastAPI or any
other framework is deferred until the V2.0.12 framework decision checkpoint.
Framework adoption requires demonstrated route, validation, schema, middleware or
command complexity; modernity alone is not justification.

## Frontend Strategy

The approved direction is React, TypeScript and Vite. The frontend will be a
separate API consumer with:

- client-side workspace routing;
- typed request and response boundaries;
- reusable accessible components;
- explicit loading, empty, stale, unavailable and error states;
- server-owned financial calculations;
- no embedded application secrets.

Frontend dependencies are not approved for installation until V2.0.2 begins.
Version 1's server-rendered dashboard remains available as a compatible private
surface during the transition.

## Design System

V2.0.3 establishes semantic colors, typography, spacing, layouts, cards, tables,
charts, icons and application states before feature work. Accessibility includes
keyboard operation, visible focus, semantic structure, contrast and reduced-motion
behavior. Semantic theme tokens must permit later dark mode, but a theme toggle
does not block initial product work.

## Authentication Strategy

Read-only V2 development may remain unauthenticated only while bound to loopback
for the trusted owner. Authentication is mandatory before any V2 write command or
non-loopback deployment.

The planned private-access model is:

- one owner identity;
- modern password hashing;
- opaque server-generated sessions with only token hashes persisted;
- `HttpOnly`, appropriate `Secure` and `SameSite` cookies;
- rotation, idle expiry, absolute expiry and logout invalidation;
- CSRF tokens and origin validation for writes;
- login throttling and authentication audit;
- environment or deployment-secret management outside Git.

Public registration, OAuth, roles and enterprise multi-tenancy are excluded.

## Command Boundary

Read routes and application commands remain distinct. Future paper and preference
commands must be authenticated, CSRF-protected, auditable and idempotent where
appropriate. HTTP handlers call existing services; they do not write through read
repositories or duplicate transition policy.

Paper commands may call `PaperTradingService` only. No command may call Dhan or
promote a paper record into live state.

## Deployment Philosophy

- Local/private operation is the default.
- Unauthenticated development binds to loopback only.
- Non-loopback or VPS deployment waits for V2.0.13 authentication.
- VPS deployment requires HTTPS and an explicitly reviewed same-origin topology.
- The production server or reverse-proxy choice is deferred until the framework
  and deployment milestones.
- Browser assets and APIs should share an authenticated origin in deployment.
- Existing operational backup, recovery and release-readiness discipline applies
  to every new persisted V2 capability.
