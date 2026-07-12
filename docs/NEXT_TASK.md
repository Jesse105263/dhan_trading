# Next Task

## Phase

Phase 2 — Option Data Platform

## Milestone

Milestone 2.6 — Option Analytics Pipeline Integration

## Objective

Integrate collection and deterministic option analytics into an operational multi-underlying pipeline without changing the production equity pipeline.

## Tasks

1. Define configured option underlyings and collection policy.
2. Add option collection and analytics stages.
3. Preserve centralized expiry selection.
4. Add bounded retries, throttling and per-underlying failure isolation.
5. Persist stage metrics and source lineage.
6. Add scheduler-safe one-shot execution.
7. Add unit and PostgreSQL integration tests.
8. Preserve all existing production behavior.

## Definition of Done

- Configured underlyings can be collected and analyzed in one operational run.
- One underlying failure does not corrupt successful results.
- Existing equity pipeline remains unchanged and green.
