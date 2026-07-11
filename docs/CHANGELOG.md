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