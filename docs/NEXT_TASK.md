# Next Task

## Phase

Phase 4 — Product Surface

## Milestone

Milestone 4.4 — AI Copilot

## Objective

Build an AI-assisted private research surface grounded exclusively in read-only platform data, with citations to platform lineage and no execution authority.

## Required Scope

- Answer research questions from stable read-only platform outputs.
- Explain rankings, selections, risk decisions, signals and backtest evidence.
- Preserve source lineage in every answer.
- Make unavailable or insufficient evidence explicit.
- Do not place orders or introduce automatic execution.

## Engineering Constraints

- Inspect the repository before choosing the AI integration boundary.
- Do not add broker-order functionality.
- Maintain backward compatibility with the production equity and option pipelines.
- Add unit tests and integration/smoke coverage appropriate to the selected implementation.
- Update documentation before Git.
- Commit only after full verification.

## Definition of Done

- AI answers are grounded in platform evidence with visible lineage.
- Missing data and model failures are visible and non-destructive.
- The AI boundary has no write or execution capability.
- Existing automated and PostgreSQL integration suites remain green.
- Documentation reflects the final architecture and operating commands.
