# Database Design

## Primary Database

PostgreSQL is the source of truth for persistent platform state.

## Current Core Tables

### instruments

Master list of supported underlying instruments.

### derivative_contracts

Normalized Dhan futures and option contracts.

Important expiry fields and indexes:

- `underlying_symbol`
- `instrument_type`
- `expiry`
- `is_active`
- Active underlying and expiry indexes
- Active option-chain strike index

The Expiry Repository derives available expiries directly from active rows in this table. A separate expiry table is intentionally not used because it would duplicate normalized contract state and introduce synchronization risk.

### derivative_import_runs

Security-master import lifecycle and summary counts.

### derivative_import_failures

Sanitized row-level derivative import failures.

### underlying_quotes

Persisted spot and equity quote batches.

### scanner_snapshots

Per-run market snapshots.

### market_features

Derived market features.

### pipeline_runs

Pipeline lifecycle, status and timing.

### pipeline_failures

Sanitized pipeline and stage failures.

### stage_metrics

Operational stage metrics and freshness.

### scheduler_locks

PostgreSQL-backed production-run locks.

## Planned Tables

- Option-chain runs.
- Option quotes.
- Option analytics.
- Market rankings.
- Trade signals.
- Backtests.
- Orders and positions.

## Option-Chain Collections

Migration `007_option_chain_collections.sql` adds:

- `option_chain_runs` for request lifecycle, status, selected expiry, spot price and collection counts.
- `option_chain_quotes` for normalized CE and PE snapshots by run, strike and option type.

Quotes and successful run completion are committed in one transaction. Failed runs retain sanitized error context without partial quote persistence.
