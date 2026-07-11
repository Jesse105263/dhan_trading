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