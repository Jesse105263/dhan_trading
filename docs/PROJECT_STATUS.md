# Project Status

## Current Phase

Phase 2 — Option Data Platform

## Completed

- Docker configured.
- PostgreSQL configured.
- Redis configured.
- Git and GitHub configured.
- Environment configuration hardened.
- Centralized pipeline and scheduler settings added.
- Structured logging added.
- Ordered database migration framework added.
- Migration checksums and version history added.
- Pipeline success and failure status persisted.
- Sanitized pipeline failure records persisted.
- Retryable failures classified.
- Explicit repository contracts added.
- PostgreSQL repository integration tests added.
- Operational stage metrics implemented.
- Stage duration persisted.
- Requested, received and written record counts persisted.
- Source-data freshness persisted.
- Production health-report command added.
- Automated migration tests added.
- Automated pipeline smoke tests added.
- Production instrument repository created.
- 209 production F&O equities loaded.
- Production Dhan quote collector created.
- 209 of 209 quotes collected and persisted.
- Real scanner snapshot stage created.
- 209 snapshots persisted per run.
- Real feature stage created.
- 209 market features persisted per run.
- CSV runtime dependency removed from the production path.
- Indian market-session validation added.
- Exchange-holiday configuration added.
- PostgreSQL scheduler locking added.
- Overlapping production runs prevented.
- Stale scheduler locks recoverable.
- Scheduler status, one-shot and recurring commands added.
- Direct pipeline execution preserved.
- Scheduler unit tests added and verified.

## Database Migrations

- `001_initial_platform_schema.sql`
- `002_pipeline_failures.sql`
- `003_stage_metrics.sql`
- `004_scheduler_foundation.sql`

## Operational Monitoring

The platform records:

- Pipeline status
- Pipeline duration
- Stage status
- Stage duration
- Records requested
- Records received
- Records written
- Source timestamp
- Data freshness
- Failure count
- Snapshot count
- Feature count
- Market-calendar status
- Scheduler-lock status

Health report command:

```bash
python -m scripts.health_report
```

Scheduler status command:

```bash
python -m scripts.scheduler status
```

## Verification

- Scheduler tests: 9 passed.
- Full automated suite: 24 passed, 3 opt-in database integration tests skipped.
- Production pipeline: 7 stages completed successfully.
- Scheduler lock table verified.
- Scheduler lock cleanup verified.
