# Next Task

## Phase

Phase 2 — Option Data Platform

## Milestone

Milestone 2.5 — Option Analytics

## Objective

Calculate deterministic option-chain features from persisted collection runs without calling Dhan APIs or implementing expiry-selection logic.

## Tasks

1. Define normalized option analytics models.
2. Read one completed option-chain run from PostgreSQL.
3. Calculate ATM strike and straddle cost.
4. Calculate call, put and nearby PCR metrics.
5. Calculate ATM and nearby implied-volatility metrics.
6. Identify call and put OI walls.
7. Calculate strike distances and liquidity coverage.
8. Persist analytics with source-run lineage.
9. Reject incomplete or stale source chains safely.
10. Add unit and PostgreSQL integration tests.
11. Preserve the production equity pipeline, scheduler, derivative import, expiry and collector behavior.

## Definition of Done

- One completed option-chain run produces persisted deterministic analytics.
- Analytics are reproducible from stored quotes without external API calls.
- Source run and expiry lineage are retained.
- Incomplete chains are rejected safely.
- Existing production and option-data tests remain green.
