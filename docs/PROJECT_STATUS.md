# Project Status

## Current Phase

Milestone 2 — Production Refactor

## Completed

- Docker configured.
- PostgreSQL configured.
- Redis configured.
- Git and GitHub configured.
- Documentation centralized.
- Environment configuration hardened.
- Production pipeline orchestration created.
- Pipeline stage interface created.
- UUID-based pipeline run IDs implemented.
- PostgreSQL health-check stage implemented.
- Production instrument repository created.
- 209 production F&O equities loaded.
- Production Dhan quote collector created.
- 209 of 209 quotes collected and persisted.
- Underlying quote repository created.
- Scanner snapshot repository created.
- Real snapshot stage created.
- 209 snapshots persisted per pipeline run.
- Production feature repository created.
- Real feature stage created.
- Price and volume changes calculated.
- Relative volume calculated from snapshot history.
- 209 of 209 feature rows persisted and validated.
- CSV runtime dependency removed from the production path.

## Current Production Pipeline

1. Database health check
2. Instrument repository lookup
3. Dhan market quote collection
4. Underlying quote persistence
5. Latest quote batch retrieval
6. Pipeline run creation
7. Scanner snapshot persistence
8. Snapshot validation
9. Snapshot history retrieval
10. Market feature calculation
11. Feature persistence
12. Feature validation
13. Ranking stage placeholder
14. Risk stage placeholder
15. Signal stage placeholder

## Database Tables

- instruments
- underlying_quotes
- option_quotes
- trade_signals
- pipeline_runs
- scanner_snapshots
- market_features

## Instrument Universe

- Production F&O equities: 209
- Exchange segment: NSE_EQ
- Test instruments: 0
- Missing quote instruments: 0

## Feature State

- Latest feature count: 209
- Distinct feature symbols: 209
- Price-change coverage: 209
- Relative-volume coverage: 209
- Lookback window: 20 runs

## Next Milestone

Build the production ranking engine using persisted market features.