# Next Task

## Phase

Phase 4 — Product Surface

## Milestone

Milestone 4.2 — Private Read-Only Dashboard

## Objective

Build a private dashboard on top of the stable `/api/v1` read-only API. The dashboard must display persisted platform outputs without recalculating analytics, mutating database state, invoking Dhan, or placing orders.

## Required Scope

- Use the read-only API as the dashboard data boundary.
- Display platform health and database readiness.
- Display recent ranking runs and ranked underlyings.
- Display contract selections and their source ranking lineage.
- Display risk approvals and rejections with sizing and exposure.
- Display generated signals with confidence, rationale, entry reference and maximum loss.
- Display replay timelines.
- Display backtest summaries and trade-level results.
- Provide stable loading, empty, error and not-found states.
- Keep the dashboard private and local by default.
- Preserve the GET-only, no-execution safety boundary.

## Engineering Constraints

- Inspect the repository before choosing the dashboard implementation.
- Do not query PostgreSQL directly from dashboard views; consume the application API.
- Do not add broker-order functionality.
- Do not add write endpoints.
- Maintain backward compatibility with the production equity and option pipelines.
- Add unit tests and integration/smoke coverage appropriate to the selected implementation.
- Update documentation before Git.
- Commit only after full verification.

## Definition of Done

- The dashboard starts through a documented command.
- Health, rankings, selections, risk, signals, replay and backtest screens are usable.
- Empty resources render correctly.
- API and dashboard errors are visible and non-destructive.
- Existing automated and PostgreSQL integration suites remain green.
- Documentation reflects the final architecture and operating commands.
