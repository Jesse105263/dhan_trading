# CHANGELOG

---

## 2026-07-05

### Infrastructure

- Installed Docker Desktop
- Verified Docker installation
- Verified Docker Compose
- Ran first Docker container

### Containers

Created:

- PostgreSQL container
- Redis container

Containers verified running.

### Python Environment

Installed:

- psycopg
- python-dotenv

Created:

- .env

### Database

Successfully connected Python to PostgreSQL.

Verified:

- Connection
- Table creation
- Insert
- Select
- Close connection

### Project

Official transition from script-based development to platform architecture.

## 2026-07-11

### Infrastructure

- Docker installed
- PostgreSQL configured
- Redis configured
- Git initialized
- Project reorganized
- Documentation centralized

### Services Added

- config.py
- database.py
- collector.py
- feature_engine.py
- ranking_engine.py
- risk_engine.py
- signal_engine.py
- snapshot_engine.py

### Database

- PostgreSQL connectivity established
- Initial schema created

## 2026-07-11

### Market Data Collection

- Added PostgreSQL-backed instrument configuration.
- Added production Dhan quote collector.
- Added live market quote ingestion from Dhan.
- Added batch persistence into `underlying_quotes`.
- Added collector execution metrics.
- Verified MCX equity collection using security ID `31181`.
- Verified DhanHQ Python client version `2.2.0`.
- Removed CSV dependency from the production collector path.

## 2026-07-11

### Instrument Repository

- Added production PostgreSQL instrument repository.
- Added bulk instrument upsert support.
- Added schema migration support for instrument metadata.
- Added `tick_size` support to the `instruments` table.
- Added F&O equity universe importer.
- Excluded NSE test and mock instruments.
- Imported 209 production F&O equities.
- Stored security IDs, lot sizes, tick sizes and exchange segments.
- Updated the collector to load instruments through the repository.
- Added multi-instrument Dhan quote collection.
- Verified 209 of 209 live quotes were collected and persisted.
- Confirmed zero missing instruments in the latest collection batch.

## 2026-07-11

### Snapshot Engine

- Added UUID-based pipeline run IDs.
- Added pipeline run status and timing metadata.
- Added PostgreSQL `pipeline_runs` table.
- Added underlying quote repository.
- Added scanner snapshot repository.
- Replaced the placeholder snapshot stage.
- Added latest quote batch retrieval.
- Added source quote timestamp validation.
- Added snapshot batch persistence.
- Added per-run snapshot count validation.
- Persisted 209 snapshots for the verified production universe.
- Added snapshot auditability by run ID.

## 2026-07-11

### Feature Engine

- Added PostgreSQL `market_features` table.
- Added production feature repository.
- Replaced the placeholder feature stage.
- Added previous-run price lookup.
- Added previous-run volume lookup.
- Added price change calculation.
- Added price change percentage calculation.
- Added volume change calculation.
- Added volume change percentage calculation.
- Added rolling average prior volume.
- Added relative-volume calculation.
- Added configurable 20-run history window.
- Added per-run feature persistence and validation.
- Verified 209 feature rows for 209 production instruments.
- Verified full snapshot-to-feature count consistency.

## 2026-07-11

### Architecture Stabilization

- Added centralized application settings.
- Added environment-driven pipeline configuration.
- Added structured application logging.
- Replaced stage lifecycle prints with structured logs.
- Added pipeline run repository.
- Added persistent pipeline success and failure states.
- Added configurable Dhan request timeout.
- Added configurable Dhan batch size.
- Added configurable feature lookback window.
- Added automated pipeline smoke tests.
- Verified successful pipeline completion persistence.
- Verified failed pipeline persistence.

## 2026-07-11

### Database Migration Framework

- Added ordered SQL migration files.
- Added `schema_migrations` table.
- Added migration version tracking.
- Added SHA-256 checksum validation.
- Added protection against modifying applied migrations.
- Added duplicate migration version validation.
- Added transactional migration execution.
- Moved schema management out of `services/database.py`.
- Reduced `services/database.py` to connection management.
- Added automated migration discovery tests.
- Added migration checksum tests.
- Added duplicate-version tests.
- Verified migration idempotency.
- Verified existing production data remained intact.

## 2026-07-11

### Repository Contracts and Integration Tests

- Added explicit repository protocols.
- Applied dependency inversion to the snapshot engine.
- Applied dependency inversion to the feature engine.
- Added snapshot insert-count validation.
- Added feature upsert-count validation.
- Added PostgreSQL instrument repository integration test.
- Added PostgreSQL underlying quote repository integration test.
- Added PostgreSQL snapshot repository integration test.
- Added PostgreSQL feature repository integration test.
- Added automatic integration-test cleanup.
- Verified no test data remained after execution.
- Verified production pipeline behavior remained unchanged.

## 2026-07-11

### Pipeline Failure Model

- Added `pipeline_failures` migration.
- Added PostgreSQL failure repository.
- Added failed-stage tracking.
- Added sanitized error persistence.
- Added retryable failure classification.
- Added symbol-level failure support.
- Added access-token, client-ID, password and JWT redaction.
- Added failure persistence to the pipeline.
- Added error sanitizer unit tests.
- Added pipeline failure smoke tests.
- Verified successful runs create zero failure records.

## 2026-07-11

### Operational Metrics

- Added `stage_metrics` database migration.
- Added PostgreSQL stage metrics repository.
- Added per-stage success and failure metrics.
- Added stage start and completion timestamps.
- Added stage duration measurement.
- Added records-requested metrics.
- Added records-received metrics.
- Added records-written metrics.
- Added source-data freshness measurement.
- Added metrics for Database, Collector, Snapshot Engine and Feature Engine.
- Added metrics support for future Ranking, Risk and Signal stages.
- Added production health-report command.
- Added stage-metrics smoke-test coverage.
- Verified seven stage metrics for a successful pipeline run.
- Verified 209 requested, received and written records across production data stages.

## 2026-07-12

### Scheduling Foundation

- Added configurable Indian market timezone and session hours.
- Added weekday, market-hours and exchange-holiday validation.
- Added PostgreSQL-backed scheduler locks.
- Added overlap prevention for recurring production runs.
- Added stale-lock recovery through lock expiry.
- Added manual calendar override while preserving lock safety.
- Added scheduler status reporting.
- Added one-shot and recurring scheduler commands.
- Preserved direct production pipeline execution through `run_pipeline.py`.
- Added scheduler unit tests covering market gating, overlap prevention, stale locks and failure cleanup.
- Added `004_scheduler_foundation.sql` migration.
- Verified all 24 automated tests pass, with 3 opt-in PostgreSQL integration tests skipped by default.
- Verified the seven-stage production pipeline completes successfully.
- Verified scheduler locks are released after execution and failure.
- Verified scheduler lock acquisition and automatic release using PostgreSQL.

## 2026-07-12

### Derivative Contract Schema

- Added `005_derivative_contracts.sql`.
- Added normalized PostgreSQL storage for futures and options contract metadata.
- Added immutable Dhan contract identity using exchange segment and security ID.
- Added trading symbol, underlying symbol, instrument type, expiry, strike and option type fields.
- Added lot size and tick size validation.
- Added active-contract lifecycle fields.
- Added database constraints for supported instrument and option types.
- Added database constraints for valid option and futures field combinations.
- Added indexes for active contracts, underlyings, expiries and strikes.
- Added derivative contract repository protocol.
- Added PostgreSQL derivative contract repository.
- Added normalization and validation for derivative contract models.
- Added active-contract, expiry and option-chain query support.
- Added contract deactivation support.
- Added repository unit tests.
- Added PostgreSQL integration tests covering upserts, queries and deactivation.
- Verified 31 automated tests pass, with 5 opt-in integration tests skipped by default.
- Verified all 5 PostgreSQL integration tests pass when enabled.
- Verified the existing seven-stage production pipeline remains green.

## 2026-07-12

### Expiry Repository and Service

- Added PostgreSQL-backed expiry availability queries derived from active derivative contracts.
- Added active contract counts per underlying, instrument type and expiry.
- Added centralized expiry selection for nearest, next and monthly expiries.
- Added minimum and maximum days-to-expiry eligibility controls.
- Added active-expiry validation and explicit not-found errors.
- Added a repository protocol for expiry data access.
- Added comprehensive expiry-service unit tests.
- Added opt-in PostgreSQL expiry repository integration tests.
- Added a production-data expiry verification command.
- Preserved the existing derivative-contract expiry query for backward compatibility.
- Added no database migration because `derivative_contracts` remains the normalized source of truth.

## 2026-07-12

### Option-Chain Collector

- Added `007_option_chain_collections.sql`.
- Added transactional option-chain run and quote persistence.
- Added PostgreSQL underlying identity resolution.
- Added centralized collector orchestration using `ExpiryService` exclusively.
- Added Dhan option-chain HTTP client.
- Added normalized option-chain request, response and quote models.
- Added complete CE/PE strike validation.
- Added sanitized failed-run persistence.
- Added command-line collection entry point.
- Added collector unit tests and PostgreSQL repository integration coverage.
- Preserved the production equity pipeline and scheduler.

## Milestone 2.5 — Option Analytics

- Added deterministic analytics models and service.
- Added completed option-chain run reader and idempotent analytics persistence.
- Added ATM, straddle, PCR, IV, OI-wall, strike-distance and liquidity-coverage calculations.
- Added stale and incomplete source-chain rejection.
- Added unit and PostgreSQL integration coverage.

## Milestone 2.6 — Option Analytics Pipeline Integration

- Added configurable multi-underlying option collection and analytics stages.
- Added bounded retry, linear backoff, request throttling, and per-underlying failure isolation.
- Added aggregate stage metrics and source-run lineage preservation.
- Added a scheduler-safe one-shot option pipeline command with a dedicated lock.
- Added unit and PostgreSQL integration coverage.
- Preserved the production equity pipeline unchanged.
