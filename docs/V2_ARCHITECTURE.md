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
- Applied migrations remain immutable; Version 2 adds only ordered, reviewed
  migrations for approved evidence stores.

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
other framework is deferred until the V2.0.13 framework decision checkpoint.
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

The frontend is isolated under `frontend/`, with its own npm package, lockfile,
TypeScript projects and build output. Version 1's server-rendered dashboard remains
available as a compatible private surface during the transition. See
`docs/FRONTEND.md` for the dependency and API-client policies.

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
- Non-loopback or VPS deployment waits for V2.0.14 authentication.
- VPS deployment requires HTTPS and an explicitly reviewed same-origin topology.
- The production server or reverse-proxy choice is deferred until the framework
  and deployment milestones.
- Browser assets and APIs should share an authenticated origin in deployment.
- Existing operational backup, recovery and release-readiness discipline applies
  to every new persisted V2 capability.

V2.0.5 implements the read-projection pattern with a thin V2 WSGI branch, a query
service for validation and freshness, and explicit SELECT projections in a dedicated
repository. `/api/v1` remains unchanged.
## Market Memory Projection

V2.0.7 treats existing immutable analytics, change, ranking, selection, risk,
signal and equity-feature tables as canonical historical storage. A dedicated
SELECT-only repository and query service expose bounded option snapshot history,
allow-listed feature evolution and exact comparisons. No parallel feature table,
migration or write-on-read behavior is introduced. Future evidence models must
reference canonical snapshot and lineage identifiers rather than untraceable
browser calculations.

## Feature Store Boundary

V2.0.8 materializes versioned numeric vectors from canonical Market Memory
observations into migration `018`. `FeatureStoreRepository` exclusively owns
feature persistence and reads; `FeatureStoreService` owns the allow-listed schema,
deterministic identity, temporal derivation and quality policy. Materialization is
an explicit offline command. HTTP exposes GET-only projections and cannot trigger
materialization.

## Historical Outcome Boundary

V2.0.9 materializes versioned outcomes from later Feature Store vectors into
migration `019`. `HistoricalOutcomeRepository` owns persistence and aggregate SQL;
`HistoricalOutcomeService` owns point-in-time filtering, objective calculations,
completion policy and deterministic identity. HTTP is GET-only and cannot invoke
materialization. Similarity and opportunity engines must consume stored outcomes.

## Similarity Boundary

V2.1.0 uses `SimilarityService` for allow-listed feature preparation,
historical-only scaling, weights, overlap policy, deterministic distance/ranking,
and post-ranking outcome attachment. `SimilarityRepository` owns Store reads and
migration `020` run/match persistence. HTTP remains thin and GET-only. Outcome
values never enter distance calculation; the browser performs no similarity or
financial policy calculation.

## Trade Opportunity Boundary

V2.1.1 consumes persisted Similarity runs and their exact Feature/Outcome lineage.
`TradeOpportunityService` owns evidence thresholds, deterministic long-reference
zones, statistics, scoring and ranking. `TradeOpportunityRepository` owns migration
`021` persistence and reads. HTTP remains GET-only and cannot materialize. The
browser presents server calculations and cannot execute, alert or paper trade.

## News and Event Boundary

V2.1.2 imports only approved provider records; the implemented adapter reads
bounded local JSON. `NewsEventService` owns validation, sanitization, identity,
explicit relevance and point-in-time leakage policy. `NewsEventRepository` owns
migration `022` persistence and reads. Context attaches after opportunity
calculation and cannot change trade fields. GET reads perform no external fetch.

## AI Trading Analyst Boundary

V2.1.3 assembles `trading-analyst-evidence-v1` from existing Feature, Memory,
Outcome, Similarity, Opportunity and Event services before synthesis. Local
deterministic synthesis is default; the existing optional model provider remains
isolated and tool-free. Refusals occur before retrieval. Citations and lineage are
application-owned, and no analyst output changes persisted calculations.

## Intelligence Release Verification

V2.1.4 extends the SELECT-only readiness repository across Feature, Outcome,
Similarity, Opportunity and Event lineage, point-in-time leakage gates, analyst
grounding and the execution-schema boundary. Migrations `001`–`022` are the
authoritative immutable inventory. Operator materializers remain explicit,
idempotent commands and are never invoked by HTTP reads.
