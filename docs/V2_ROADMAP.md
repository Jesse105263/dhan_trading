# Dhan Trading Platform — Version 2 Roadmap

## Status

Approved. Version 2 is the active roadmap. Version 1 is complete, verified and
preserved as the stable backend baseline.

## Roadmap Rules

- Use `V2.0.x` numbering; do not continue Version 1 milestone numbering.
- Work on one focused milestone at a time.
- Prefer product delivery over speculative infrastructure.
- Add only the API projections required by the current workspace.
- Preserve `/api/v1`, existing services, repositories and schema unless a later
  approved milestone provides evidence for change.
- Read-only workflows precede authenticated commands.
- No milestone introduces live broker execution.

## Ordered Milestones

### V2.0.1 — Architecture & Product Decisions

Status: Complete.

Establish the product definition, architecture, technology direction, compatibility
policy, safety boundaries and approved roadmap. No application code, dependencies
or database changes.

### V2.0.2 — Frontend Project Foundation

Status: Implemented and verified; pending repository-owner review.

Create the React, TypeScript and Vite project, package lock, test/lint tooling,
route skeleton, API-client conventions, development proxy and production build
structure. This is frontend-only and requires explicit dependency-install approval.

### V2.0.3 — Design System

Create semantic tokens and reusable accessible layouts, cards, tables, controls,
chart framing, icons and loading/empty/stale/error states. Establish dark-mode-ready
tokens without requiring a theme toggle.

### V2.0.4 — Application Shell

Build responsive navigation, workspace routing, global status, page composition,
error boundaries and placeholder routes. Remain read-only and loopback-only.

### V2.0.5 — Market Overview & Opportunity Scanner

Present current health and freshness summaries plus filterable persisted rankings
and opportunity context. Add only required read projections; never trigger a
pipeline or recalculate an opportunity.

### V2.0.6 — Symbol Research Workspace

Add symbol search, persisted underlying context, expiry-aware option-chain
exploration and option-analytics history/visualization. Do not call Dhan or
reimplement expiry or analytics policy.

### V2.0.7 — Signals & Decision Lineage Workspace

Present ranking explanations, contract selections, risk approvals/rejections,
signals, sizing, maximum loss and exact upstream lineage. Remain read-only.

### V2.0.8 — Replay & Backtesting Workspace

Visualize replay timelines, backtest summaries, trade logs, equity curves,
drawdowns, costs, exits and skipped marks from persisted results only.

### V2.0.9 — Paper Portfolio Workspace

Present paper orders, fills, open/closed positions, P&L, mark freshness, events and
signal lineage. This milestone is read-only and exposes no open/mark/close controls.

### V2.0.10 — Operations Workspace

Combine platform health, pipeline freshness, scheduler status, persisted failures,
alert history and operational audit into one read-only workspace. Reading alert
history must not generate, retry or deliver an alert.

### V2.0.11 — Grounded Copilot Workspace

Add the question, context, evidence and citation experience using the existing
Copilot architecture. Local deterministic synthesis remains the default; execution
requests remain refusals and providers receive no tools.

### V2.0.12 — API Framework Decision Checkpoint

Review actual V2 route count, validation duplication, schema drift, frontend type
maintenance, middleware and upcoming command needs. Continue WSGI unless evidence
justifies a narrowly scoped framework migration. This milestone does not assume
FastAPI as its outcome.

### V2.0.13 — Private Authentication & Session Security

Add one-owner authentication, password hashing, opaque sessions, secure cookies,
expiry/revocation, CSRF, origin validation, throttling and audit. This milestone is
security-sensitive, dependency-installing and migration-requiring. It must finish
before commands or non-loopback deployment.

### V2.0.14 — Authenticated Paper-Trading Commands

Expose explicitly confirmed, authenticated and auditable paper open, mark and close
commands through `PaperTradingService`. Require CSRF and idempotency. This is
state-changing but must retain zero Dhan, broker or paper-to-live capability.

### V2.0.15 — Alert Preferences

Add authenticated source/severity preferences, channel enablement and audited
changes without returning destination secrets to the browser. Saving preferences
must not implicitly send alerts.

### V2.0.16 — Preferences & Saved Views

Add demonstrated owner preferences such as scanner filters, table density, theme
and saved research views. Prefer browser-local storage unless cross-device or
backup requirements justify persistence.

### V2.0.17 — Private Deployment & Release Hardening

Verify the production frontend build, same-origin topology, HTTPS guidance,
security headers, cookies, proxy behavior, backups, V1 compatibility and the full
no-live-execution boundary. Local deployment remains the default.

## Milestone Classification

- Documentation-only: V2.0.1 and the decision output of V2.0.12.
- Frontend foundation/design: V2.0.2–V2.0.4.
- Read-only product workspaces: V2.0.5–V2.0.11.
- Authentication/security: V2.0.13.
- State-changing: V2.0.14–V2.0.16 when server persistence is selected.
- Migration-requiring: V2.0.13; V2.0.14–V2.0.16 only when their approved designs
  require new audit, idempotency or preference state.
- External dependency installation: V2.0.2, V2.0.3 if a chart package is selected,
  and V2.0.13; any framework dependency depends on V2.0.12.
- Highest accidental live-execution risk: V2.0.14. Its verification must prove no
  broker client, live-order table, execution route or paper promotion exists.

## Current Milestone

V2.0.2 — Frontend Project Foundation.

## Next Milestone After Review

V2.0.3 — Design System. It must not begin until V2.0.2 is reviewed and explicitly
approved by the repository owner.
