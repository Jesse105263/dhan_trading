# Project Status

## Current Phase

Architecture Stabilization

## Completed

- Docker configured.
- PostgreSQL configured.
- Redis configured.
- Git and GitHub configured.
- Documentation centralized.
- Environment configuration hardened.
- Centralized pipeline settings added.
- Structured logging added.
- Pipeline run repository added.
- Pipeline success persistence added.
- Pipeline failure persistence added.
- Automated smoke tests added.
- Production pipeline orchestration created.
- UUID-based pipeline run IDs implemented.
- Production instrument repository created.
- 209 production F&O equities loaded.
- Production Dhan quote collector created.
- 209 of 209 quotes collected and persisted.
- Scanner snapshot repository created.
- Real snapshot stage created.
- 209 snapshots persisted per pipeline run.
- Production feature repository created.
- Real feature stage created.
- 209 feature rows persisted and validated.
- CSV runtime dependency removed from the production path.

## Current Production Pipeline

1. Pipeline run creation
2. Database health check
3. Instrument repository lookup
4. Dhan market quote collection
5. Underlying quote persistence
6. Scanner snapshot persistence
7. Snapshot validation
8. Snapshot history retrieval
9. Market feature calculation
10. Feature persistence
11. Feature validation
12. Ranking stage placeholder
13. Risk stage placeholder
14. Signal stage placeholder
15. Pipeline completion or failure persistence

## Configuration

Environment-driven values:

- LOG_LEVEL
- DHAN_REQUEST_TIMEOUT_SECONDS
- DHAN_MAX_INSTRUMENTS_PER_REQUEST
- FEATURE_LOOKBACK_RUNS

## Automated Tests

- Successful pipeline smoke test
- Failed pipeline smoke test

## Next Milestone

Create a proper migration framework and move schema changes out of `services/database.py`.