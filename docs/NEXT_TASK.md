# Next Task

## Phase

Phase 2 — Option Data Platform

## Milestone

Milestone 2.7 — Option Analytics History and Change Detection

## Objective

Build reliable time-series retrieval and deterministic change features across completed option analytics snapshots.

## Tasks

1. Add historical analytics repository queries by underlying and expiry.
2. Calculate OI, PCR, IV, ATM straddle, wall and liquidity changes.
3. Preserve source-run and calculation lineage.
4. Reject incomparable or unordered snapshots.
5. Add unit and PostgreSQL integration tests.
6. Add a production verification command.
7. Preserve all existing production behavior.

## Definition of Done

- Consecutive completed analytics snapshots can be compared deterministically.
- Change features are queryable with explicit lineage.
- Existing equity and option operational pipelines remain green.
