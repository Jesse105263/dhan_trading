# Next Task

## Phase

Phase 4 — Product Surface

## Milestone

Milestone 4.5 — Paper Trading

## Objective

Build isolated paper-trade simulation from persisted signals with complete attribution and no live broker-order submission.

## Required Scope

- Create simulated orders and positions from persisted approved signals.
- Preserve signal, risk, selection and market-data lineage.
- Track simulated fills, position state and P&L.
- Keep paper state isolated from live broker and production source records.
- Do not submit orders to Dhan or introduce automatic live execution.

## Engineering Constraints

- Inspect the repository before choosing the paper-trading boundary.
- Do not add broker-order functionality.
- Maintain backward compatibility with the production equity and option pipelines.
- Add unit tests and integration/smoke coverage appropriate to the selected implementation.
- Update documentation before Git.
- Commit only after full verification.

## Definition of Done

- Paper orders and positions are reproducible and fully attributed.
- Missing prices and invalid transitions are visible and non-destructive.
- No paper-trading component can submit a live broker order.
- Existing automated and PostgreSQL integration suites remain green.
- Documentation reflects the final architecture and operating commands.
