# Next Task

## Phase

Phase 4 — Product Surface

## Milestone

Milestone 4.3 — Alerts

## Objective

Build private alerts from persisted platform outputs while preserving deterministic, read-only research and the no-execution boundary.

## Required Scope

- Define alert events for signals, risk decisions and pipeline health.
- Keep alert generation downstream of persisted platform state.
- Add configurable private delivery channels and failure handling.
- Preserve lineage, deduplication and auditability.
- Do not place orders or introduce automatic execution.

## Engineering Constraints

- Inspect the repository before choosing the alert implementation.
- Do not add broker-order functionality.
- Maintain backward compatibility with the production equity and option pipelines.
- Add unit tests and integration/smoke coverage appropriate to the selected implementation.
- Update documentation before Git.
- Commit only after full verification.

## Definition of Done

- Alert event and delivery boundaries are documented.
- Duplicate alerts are prevented.
- Delivery failures are visible and non-destructive.
- Existing automated and PostgreSQL integration suites remain green.
- Documentation reflects the final architecture and operating commands.
