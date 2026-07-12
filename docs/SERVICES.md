# Services

## Production Services

### collector

Downloads live underlying prices from Dhan and persists normalized quote batches.

### derivative_security_master

Downloads, validates and imports supported derivative contracts into PostgreSQL.

### expiry_repository

Reads active expiry availability from `derivative_contracts`.

Responsibilities:

- List active expiries for one underlying and instrument type.
- Return active contract counts for each expiry.
- Validate that a specific expiry exists.
- Count underlyings with active eligible expiries.

It contains database access only and no expiry-selection policy.

### expiry_service

Owns all expiry-selection and expiry-validation policy.

Responsibilities:

- Select nearest eligible expiry.
- Apply minimum and maximum days-to-expiry windows.
- Select the next expiry after a known expiry.
- Identify the last available expiry in each calendar month.
- Select the nearest monthly expiry.
- Validate requested expiries against active contracts.

Downstream collectors and strategy components must not implement independent expiry-selection logic.

### feature_engine

Calculates normalized market features.

### ranking_engine

Ranks opportunities.

### risk_engine

Applies deterministic risk controls.

### signal_engine

Creates trade signals.

### scheduler

Runs market-calendar-aware periodic jobs and prevents overlapping production runs.

### ai_engine

Uses Claude or GPT for research and explanations. It never participates in live execution.

## Planned Services

- Option-chain collector.
- Option analytics engine.
- Dashboard API.
- Alert service.
- Backtesting and replay services.

### option_chain_collector

Collects and persists one complete Dhan option chain.

Responsibilities:

- Resolve the underlying security identity from PostgreSQL.
- Delegate all expiry selection and validation to `ExpiryService`.
- Fetch one option chain through `DhanOptionChainClient`.
- Normalize CE and PE quote snapshots.
- Reject incomplete or malformed strike data.
- Persist run metadata and quotes transactionally.
- Persist sanitized failure details for started runs.

### option_chain_repository

Owns database access for option-chain collection runs and quote snapshots. It contains no expiry-selection policy or API parsing logic.

## Option Analytics Service

- `services/option_analytics_models.py`: analytics requests, completed-chain input and normalized output models.
- `services/option_analytics_repository.py`: reads completed option-chain runs and upserts source-linked analytics.
- `services/option_analytics_service.py`: validates source quality and calculates ATM, straddle, PCR, IV, OI-wall and coverage metrics.
- `scripts/analyze_option_chain.py`: calculates and persists analytics for a completed collection run.

## Option Data Pipeline

- `services.option_data_pipeline.OptionCollectionStage`: configured multi-underlying collection, bounded retry, throttling, metrics, and failure isolation.
- `services.option_data_pipeline.OptionAnalyticsStage`: deterministic analytics for successful source runs only.
- `services.option_data_pipeline.build_option_data_pipeline`: builds the dedicated operational option pipeline without changing the equity pipeline.
- `scripts.run_option_data_pipeline`: scheduler-safe one-shot runner; use `--force` outside market hours.

## OptionAnalyticsHistoryRepository

Provides ordered analytics history, resolves the immediately preceding comparable snapshot and persists idempotent change records with full lineage.

## OptionAnalyticsHistoryService

Validates snapshot comparability and calculates deterministic changes for spot, ATM straddle, total and nearby OI/PCR, ATM and nearby IV, call/put OI walls, price coverage and liquidity coverage.

## compare_option_analytics

Command-line verification entry point:

```bash
python -m scripts.compare_option_analytics <current-analytics-id>
```
