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
- Derivative-contract schema added.
- Dhan derivative contract identity protected by database constraints.
- Active contract lifecycle added.
- Contract indexes added for underlying, expiry, strike and activity.
- Derivative contract repository contract added.
- PostgreSQL derivative contract repository added.
- Derivative contract normalization and validation added.
- Unit and PostgreSQL integration coverage added for derivative contracts.
- Existing production equity pipeline preserved.

## Database Migrations

- `001_initial_platform_schema.sql`
- `002_pipeline_failures.sql`
- `003_stage_metrics.sql`
- `004_scheduler_foundation.sql`
- `005_derivative_contracts.sql`
- `006_derivative_security_master_imports.sql`

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

- Derivative contract unit tests: 5 passed.
- Full automated suite: 31 passed, 5 opt-in database integration tests skipped.
- PostgreSQL integration suite: 5 passed.
- Production pipeline: 7 stages completed successfully.
- Database stage: 10 required tables and 5 applied migrations.
- Existing scheduler and market-core behavior remained green.

## Milestone 2.2 — Security Master Import

Status: Complete.

- Dhan derivative security master import implemented.
- Import is idempotent.
- Active contract lifecycle preserved.
- Import run and failure persistence added.
- Production import verified with 215,940 rows processed, 68,406 derivative contracts imported and zero rejected rows.

## Milestone 2.3 — Expiry Repository

Status: Complete.

- PostgreSQL-backed Expiry Repository added.
- Expiry availability derived from active derivative contracts.
- Contract counts exposed per expiry.
- Central Expiry Service added.
- Nearest, next and monthly expiry selection implemented.
- Minimum and maximum days-to-expiry windows implemented.
- Active expiry validation implemented.
- Repository protocol added.
- Unit and PostgreSQL integration coverage added.
- Production verification command added.
- Existing derivative-contract expiry query preserved for backward compatibility.
- No database migration required.

## Current Verification

- Full automated suite: 49 tests passed or skipped as expected.
- Non-database tests: 42 passed.
- Opt-in PostgreSQL tests: 7 skipped in environments without PostgreSQL.
- Expiry Service unit tests: 11 passed.
- Existing pipeline and scheduler tests remained green.
- PostgreSQL integration and imported-production-data verification must be run against the project database with `RUN_DB_INTEGRATION_TESTS=1`.


## Milestone 2.4 — Option-Chain Collector

Status: Implementation complete; local and PostgreSQL verification required before commit.

- Transactional collection-run and quote schema added.
- Underlying security identity resolved from PostgreSQL.
- Expiry selection and validation delegated exclusively to `ExpiryService`.
- Dhan option-chain client and collector orchestration added.
- CE/PE strike completeness validation added.
- Sanitized failed-run persistence added.
- Unit and PostgreSQL integration tests added.
- Existing equity pipeline and scheduler preserved.
