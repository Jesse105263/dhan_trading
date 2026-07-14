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
- Every milestone must increase the system's ability to discover statistically
  better trading opportunities; otherwise defer it.

## Ordered Milestones

### V2.0.1 — Architecture & Product Decisions

Status: Complete.

Establish the product definition, architecture, technology direction, compatibility
policy, safety boundaries and approved roadmap. No application code, dependencies
or database changes.

### V2.0.2 — Frontend Project Foundation

Status: Complete.

Create the React, TypeScript and Vite project, package lock, test/lint tooling,
route skeleton, API-client conventions, development proxy and production build
structure. This is frontend-only and requires explicit dependency-install approval.

### V2.0.3 — Design System

Status: Complete.

Create semantic tokens and reusable accessible layouts, cards, tables, controls,
chart framing, icons and loading/empty/stale/error states. Establish dark-mode-ready
tokens without requiring a theme toggle.

### V2.0.4 — Application Shell

Status: Complete.

Build responsive navigation, workspace routing, global status, page composition,
error boundaries and placeholder routes. Remain read-only and loopback-only.

### V2.0.5 — Market Overview & Opportunity Scanner

Status: Complete.

Present current health and freshness summaries plus filterable persisted rankings
and opportunity context. Add only required read projections; never trigger a
pipeline or recalculate an opportunity.

### V2.0.6 — Symbol Research Workspace

Status: Complete.

Add symbol search, persisted underlying context, expiry-aware option-chain
exploration and option-analytics history/visualization. Do not call Dhan or
reimplement expiry or analytics policy.

### V2.0.7 — Market Memory Foundation

Status: Complete.

Unify existing immutable analytics, ranking, selection, risk, signal and equity
feature records behind bounded historical snapshot, feature-history and comparison
queries. Add the read-only Market Memory workspace. Do not invent absent features,
duplicate canonical records, trigger pipelines or generate recommendations.

### V2.0.8 — Feature Store

Status: Complete.

Establish versioned, reusable feature vectors derived only from supported persisted
market observations. Preserve source timestamps, feature definitions, data-quality
state and exact Market Memory lineage. Do not generate recommendations.

### V2.0.9 — Historical Outcome Engine

Status: Complete.

Measure subsequent historical outcomes for eligible observations using explicit,
auditable outcome definitions. Preserve point-in-time correctness and prevent
future information from leaking into historical evidence.

### V2.1.0 — Similarity Engine

Find historically similar feature-store observations and return their exact source
snapshots and measured outcomes. Similarity is evidence retrieval, not a trade
recommendation.

Status: Complete.

### V2.1.1 — Trade Opportunity Engine

Generate evidence-backed opportunity assessments from current features, historical
outcomes and similar observations. Keep recommendations separate from execution
and expose assumptions, evidence quality, expected value and lineage explicitly.

Status: Complete.

### V2.1.2 — News & Event Intelligence

Add time-aware news and market-event evidence with source attribution and explicit
relevance to symbols and expiries. External evidence must not bypass application
services or become an execution instruction.

Status: Implemented and verified; pending repository-owner review.

### V2.1.3 — AI Trading Analyst

Provide a grounded analyst experience over Market Memory, feature vectors,
historical outcomes, similar observations, opportunity evidence and attributed
events. The analyst has no execution tools and cannot place trades.

## Milestone Classification

- Documentation-only: V2.0.1.
- Frontend foundation/design: V2.0.2–V2.0.4.
- Read-only product workspaces and Market Memory: V2.0.5–V2.0.7.
- Historical evidence foundations: V2.0.8–V2.1.0.
- Evidence-backed intelligence: V2.1.1–V2.1.3.
- No approved milestone in this sequence adds broker execution, a live-order
  endpoint, LLM execution tools or a paper-to-live path.

## Current Milestone

V2.1.2 — News & Event Intelligence.

## Next Milestone After Review

V2.1.3 — AI Trading Analyst. It must not begin until V2.1.2 is
reviewed and explicitly approved by the repository owner.
