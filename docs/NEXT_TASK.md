# Next Task

## Phase

Stable Market Core

## Milestone

Scheduling Foundation

## Objective

Create a safe scheduling foundation for recurring market-day pipeline execution.

## Tasks

1. Add Indian market-session configuration.
2. Add weekday and market-hours validation.
3. Add exchange-holiday support.
4. Add PostgreSQL run locking.
5. Prevent overlapping pipeline runs.
6. Add stale-lock recovery.
7. Add manual execution override.
8. Add scheduler status reporting.
9. Add scheduler unit tests.
10. Preserve direct pipeline execution.

## Definition of Done

- The pipeline can run on a controlled recurring schedule.
- Runs outside configured market hours are skipped by default.
- Exchange holidays can be configured.
- Concurrent production runs are prevented.
- Stale locks can be recovered safely.
- Manual runs remain available.
- Scheduler behavior has automated test coverage.