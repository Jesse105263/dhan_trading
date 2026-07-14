# Architectural Decisions

Decision 001

Docker manages all infrastructure.

Reason

Portable development.

---

Decision 002

PostgreSQL is the primary database.

Reason

Scalability.

---

Decision 003

Redis stores only real-time data.

Reason

Performance.

---

Decision 004

CSV files are temporary.

Reason

Database-first architecture.

---

Decision 005

LLMs never execute trades.

Reason

Trading must remain deterministic.

---

Decision 006

One milestone per session.

Reason

Maintain documentation quality.

---

Decision 007

Every command must specify:

- Application
- Folder
- Terminal
- Virtual Environment

Reason

Remove ambiguity.

---

Decision 008

No versioned filenames.

Use Git history instead.

Reason

Cleaner project.
---

Decision 009

Available expiries are derived from active `derivative_contracts` rows rather than stored in a separate table.

Reason

Derivative contracts are already the normalized source of truth. Duplicating expiry state would create avoidable consistency and lifecycle risks.

---

Decision 010

All expiry-selection policy belongs to `ExpiryService`; repositories provide data only.

Reason

Collectors, strategies and future contract-selection components must use one deterministic implementation for eligibility, nearest-expiry, next-expiry and monthly-expiry behavior.

## ADR — Persist option-chain runs separately from legacy option quotes

The production collector writes to normalized `option_chain_runs` and `option_chain_quotes` tables rather than the legacy `option_quotes` table. A run ID provides transactional lineage, request metrics, failure state and replayability while preserving the old table for backward compatibility.

## Option analytics are deterministic and source-run scoped

Option analytics are calculated only from persisted `option_chain_quotes`. The analytics layer cannot call market-data APIs or perform expiry selection. ATM ties resolve to the lower strike. Nearby metrics use an explicit count of strikes on each side of ATM. A source run is rejected when stale, incomplete or internally inconsistent. Reprocessing is idempotent by `source_run_id`.

## ADR — Dedicated option data pipeline

The option data workflow remains separate from the production equity pipeline. This preserves backward compatibility and allows option-specific retry, throttling, symbol configuration, failure isolation, and scheduler locking without changing stable equity behavior. Partial per-underlying failure is recorded but does not fail the operational run when other configured underlyings succeed.

## ADR — Consecutive Analytics Comparison

Option changes are calculated only between a snapshot and its immediately preceding persisted analytics snapshot for the same normalized underlying and expiry. Comparisons across expiries, underlyings, duplicate snapshots or non-increasing capture times are rejected. This prevents downstream ranking and signals from silently comparing incompatible market states.

## Ranking methodology

Ranking v1 uses deterministic min-max normalization across the eligible universe with fixed weights: liquidity 35%, activity 30%, volatility 20%, directional structure 15%.

## Contract selection policy

Contract selection consumes persisted ranking runs and the exact option-chain source run linked through analytics. It selects at most one CE and one PE per ranked underlying using deterministic distance, spread, open-interest, volume, strike and security-id ordering. Downstream components must not reimplement contract eligibility.

## Long-option risk model

For Version 1, contract selection produces long-option candidates only. Maximum loss is therefore defined as premium paid. Position size is the largest whole-lot quantity that satisfies the configured available-capital, single-trade loss, total exposure and per-underlying concentration constraints. Both approvals and rejections are persisted for auditability.

## Deterministic long-option signal policy

Version 1 signals are generated only from approved risk assessments. A CE approval maps to a bullish buy-to-open signal and a PE approval maps to a bearish buy-to-open signal. When both sides exist for the same underlying and expiry, each is explicitly marked as a leg of a long-straddle context. Confidence is a fixed weighted combination of ranking, contract, liquidity, activity and volatility scores. Signal generation never sends orders.

## Persisted-lineage replay

Market replay consumes only committed database state. Live APIs and recomputation are excluded so identical source lineage produces the same ordered event types and payload semantics.

### Backtesting uses persisted marks only
Backtests use signal entry references and subsequent persisted `option_chain_quotes`. Missing future marks are recorded as skipped trades rather than fabricated prices.

## Decision: Standard-library, read-only API boundary

The first product API uses WSGI from the Python standard library and adds no web-framework dependency. All routes are GET-only, versioned under `/api/v1`, bounded to 100 rows per list request and backed by a dedicated read repository. This keeps the production dependency surface small while establishing a stable HTTP contract.

## Decision: Separate HTTP-only dashboard boundary

The private dashboard is a standard-library WSGI application and a separate process from the read API. It uses a small HTTP GET client rather than importing the API repository or database layer. Server-side rendering keeps the dashboard dependency-free and same-origin browser behavior simple, while the explicit API base URL preserves the `/api/v1` boundary. Both processes bind to loopback by default.

## Decision: Persist alerts before isolated delivery

Alert events are derived only from committed signal, risk and pipeline records. The unique `(source_type, source_id)` identity makes generation idempotent. Delivery is a separate adapter step, with every attempt persisted and sanitized. A successfully delivered alert/channel pair is never delivered again; failed channels can retry without duplicating the alert event. Delivery cannot mutate source data or invoke broker execution.

## Decision: Application-grounded Copilot with provider isolation

Copilot evidence retrieval is deterministic and occurs only through `/api/v1` before any model call. The application, not the model, selects resources, filters symbols and appends verified run/item citations. Providers receive evidence text but no tools or credentials for PostgreSQL, Dhan or execution. Local synthesis is always available, and provider failures fall back without losing evidence or exposing secrets.

## Decision: Paper orders are isolated state, never executable intent

Paper positions originate only from persisted approved signals and are priced only with persisted completed option-chain marks. Orders, fills, positions and events use dedicated tables with full upstream lineage. A paper order cannot be converted, promoted or submitted to Dhan. Missing marks create explicit rejection or transition errors without fabricating prices.

## Decision: Release verification is read-only and fail-closed

Version 1.0 readiness checks use a dedicated repository containing SELECT statements
only. The service compares migrations `001`–`017`, audits populated lineage and
operational datasets, and treats violations or incomplete required checks as FAIL.
An optional dataset with no records is SKIP rather than fabricated evidence.

Backup, restore, fresh migration and failure injection are operator-controlled
drills against explicitly isolated databases. The verifier cannot create, restore,
delete or migrate a database and cannot modify production records.

## Decision: Version 2 is a product-surface evolution

Version 2 builds a polished private trading-intelligence and paper-trading
workspace on the verified Version 1 backend. Existing repositories, services,
database schema, production pipelines and safety guarantees remain the default.
Components are changed only when a focused milestone demonstrates a product or
operational need.

## Decision: React, TypeScript and Vite frontend

The Version 2 interactive workspace uses React, TypeScript and Vite. This supports
reusable accessible components, dense data tables, charts and client-side workspace
navigation while preserving a strict HTTP API boundary. The Version 1 dashboard
remains available during migration. Dependencies are installed only when V2.0.2
is explicitly authorized.

## Decision: Isolated top-level frontend package

The Version 2 Node project lives under `frontend/` with its own package manifest,
lockfile, TypeScript configuration, tests and generated output. This keeps npm
tooling and dependencies separate from the stable Python root while allowing both
applications to remain in one repository. Generated dependencies, builds and
coverage are ignored.

React and React DOM provide rendering; React Router establishes the approved route
foundation. Native `fetch` provides HTTP transport, so no HTTP-client dependency
is introduced. Vite and TypeScript own builds and type checking; Vitest and Testing
Library verify accessible behavior; ESLint and Prettier have separate correctness
and formatting responsibilities. No state library, UI kit, chart library or
authentication package is justified in V2.0.2.

## Decision: Preserve WSGI and `/api/v1` initially

The stable GET-only `/api/v1` contract and standard-library WSGI implementation
remain unchanged. Version 2 adds only the read projections required by each
workspace, under a compatible `/api/v2` boundary. A framework change is deferred
to V2.0.13 and requires evidence of material routing, validation, schema,
middleware or command complexity. FastAPI is not approved merely because it is a
modern framework.

## Decision: Product-first milestone order with a design system

After architecture documentation, Version 2 establishes the frontend foundation,
design system and application shell before feature workspaces. Market, research,
signals, replay/backtesting, paper portfolio, operations and Copilot workspaces are
built read-only before authentication and commands.

The design system uses semantic CSS custom properties and accessible React
primitives without adopting a third-party component or CSS framework. Components
remain product-agnostic and contain no data or trading policy. `lucide-react` is
the single icon source because its SVG components are consistent, tree-shakeable
and do not require an icon font.

The Operations Workspace combines health, pipeline freshness, scheduler status,
failures, alert history and operational audit. Reading alert records cannot
generate, retry or deliver alerts.

## Decision: Authentication follows read-only workflow discovery

One-owner, loopback-only read development may precede authentication. Private
authentication is mandatory before state-changing V2 commands or non-loopback
deployment. The planned boundary uses secure opaque sessions, password hashing,
CSRF protection, origin validation, expiry/revocation and authentication audit;
it does not introduce public registration or multi-tenancy.

## Decision: Persisted-source freshness bands

Market freshness is presentation policy: current through 15 minutes, aging through
60 minutes, stale after 60 minutes and unavailable without a source timestamp. The
API returns the persisted timestamp; the browser never implies data is live or
recalculates financial analytics.
## V2.0.7 Reuses Canonical Persisted Observations as the Feature Store

Decision: expose existing immutable analytics, changes, rankings, selections,
risk, signals and equity features through a unified SELECT-only Market Memory
projection. Do not duplicate them in a new schema merely to rename them a feature
store. The canonical option snapshot ID is `analytics_id`; comparisons use exact
snapshots and allow-listed persisted fields.

Reason: the current tables already preserve observation timestamps, reusable
features and foreign-key lineage. Duplication would add synchronization ambiguity
without supplying new evidence. Metrics absent from persisted data remain
unsupported until a separately approved pipeline can calculate and persist them.
## V2.0.8 Uses Normalized, Versioned Feature Vectors

Decision: persist one deterministic `option-observation-v1` vector per canonical
analytics snapshot, with normalized numeric values and exact analytics, change and
ranking lineage. Keep nulls explicit and report `COMPLETE` or `PARTIAL` quality;
do not impute unavailable metrics.

Reason: Historical Outcome and Similarity engines need stable point-in-time inputs
that can be queried and compared without rebuilding features differently in every
consumer. A schema version permits later feature definitions without rewriting
historical meaning.
## V2.0.9 Uses Expiry-Capped Observed Outcomes

Decision: calculate `underlying-through-expiry-v1` outcomes only from later
Feature Store observations sharing symbol and expiry. Persist partial excursions
when measurable, but classify expiry return and win/loss only with an expiry-date
observation.

Reason: sparse snapshots can objectively establish an observed path but cannot
establish unobserved prices or an expiry result. Explicit partial state prevents
look-ahead, interpolation and false labels from contaminating future similarity
and opportunity statistics.

## V2.1.0 Uses Transparent Persisted Similarity Runs

Decision: use min-max normalized weighted Manhattan distance over a versioned
feature allow-list. Operator-materialized runs and matches have deterministic
identifiers; GET analysis is non-mutating. Outcomes attach only after ranking.

Reason: the method is null-safe, inspectable and reproducible on the current
small local dataset, needs no ML/vector dependency, and preserves evidence
lineage for V2.1.1. Vector databases, ML frameworks, opaque embeddings and
outcome-informed distance are rejected.

## V2.1.1 Requires Classified Evidence and Uses Underlying Reference Zones

Decision: require five expiry-complete matched outcomes before emitting long
reference levels. Calculate pullback entry, adverse-excursion stop and two
favourable-excursion targets from deterministic MAE/MFE quantiles. Keep all
recommendation fields null for insufficient or non-positive evidence.

Reason: Historical Outcomes measure underlying spot paths, not option premiums.
This policy supports traceable evidence without inventing option prices or
confidence. The ranking score orders eligible records and is not a probability.

## V2.1.2 Uses Explicit Relevance and Publication-Time Leakage Gates

Decision: link events only by exact provider-supplied symbols or explicit
market-wide scope. Preserve sectors without expanding them absent an authoritative
mapping. Permit predictive context only when publication time proves the event was
known at observation; later events remain outcome context.

Reason: deterministic identifiers and timestamps are auditable. Embeddings,
sentiment and inferred relationships would introduce unsupported associations and
future leakage. Event context remains separate from opportunity calculations.
