# Next Task

## Phase

Phase 2 — Option Data Platform

## Milestone

Milestone 2.4 — Option-Chain Collector

## Objective

Collect and persist one complete option chain using the centralized Expiry Service for all expiry selection and validation.

## Tasks

1. Define the option-chain collection request and response models.
2. Resolve the underlying security identity from PostgreSQL.
3. Select and validate expiry only through `ExpiryService`.
4. Fetch one Dhan option chain.
5. Normalize call and put quote records.
6. Persist option-chain run metadata.
7. Persist option quote snapshots.
8. Validate expected strikes and option sides.
9. Isolate and sanitize API and symbol-level failures.
10. Add request, response and persistence metrics.
11. Add unit and PostgreSQL integration tests.
12. Preserve the existing equity pipeline and scheduler.

## Definition of Done

- One supported underlying option chain is collected successfully.
- No collector or downstream component implements independent expiry-selection logic.
- The selected expiry is active and validated through `ExpiryService`.
- Option-chain metadata and quotes are persisted transactionally.
- Malformed or incomplete chain responses are rejected safely.
- Existing production pipeline, scheduler, derivative import and expiry tests remain green.
