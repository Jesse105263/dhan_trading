# Next Task

## Phase

Phase 3 — Ranking and Risk

## Milestone

Milestone 3.1 — Ranking Engine

## Objective

Build deterministic, explainable ranking across the latest comparable option analytics and change snapshots.

## Tasks

1. Define ranking inputs and eligibility rules.
2. Add normalized component scores for liquidity, activity, volatility and directional structure.
3. Persist total scores with component-level explainability and lineage.
4. Reject stale, incomplete or incomparable inputs.
5. Add unit and PostgreSQL integration tests.
6. Add a production verification command.
7. Preserve all existing production behavior.

## Definition of Done

- Eligible underlyings can be ranked deterministically from persisted analytics.
- Every score is queryable with source and change lineage.
- Existing equity and option operational pipelines remain green.
