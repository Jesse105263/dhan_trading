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

## OptionRankingService

Filters stale or illiquid candidates, calculates explainable normalized component scores, applies deterministic tie-breaking and persists a ranking batch through `OptionRankingRepository`.

## OptionContractSelectionService

Selects tradeable CE and PE contracts from ranked underlyings using centralized deterministic eligibility and tie-breaking rules. `OptionContractSelectionRepository` performs all database reads and persistence.

## OptionRiskService

- Reads a completed contract-selection run.
- Applies portfolio-aware capital, maximum-loss and concentration limits.
- Sizes approved contracts in whole lots.
- Persists approvals and rejections with full upstream lineage.
- Exposes `scripts.assess_option_risk` for production verification.

## OptionSignalService

Generates explainable long-option signals from approved risk assessments, computes fixed-methodology confidence, identifies paired straddle legs, validates expiry and position data, and persists immutable lineage.

## Market Replay Service

Loads a complete signal lineage, validates timestamp and entity consistency, emits six ordered lifecycle events per signal, and persists the replay atomically.

### `OptionBacktestService`
Applies deterministic target, stop-loss, last-available exit, slippage and transaction-cost rules to persisted signals and market marks.

## Read-Only API

- `services/read_api_repository.py` — read-only queries for rankings, selections, risk, signals, replay and backtests.
- `app/read_api.py` — versioned WSGI routing, validation, error handling and JSON serialization.
- `scripts/run_read_api.py` — local/private HTTP server entry point.

Routes:
- `GET /health`
- `GET /api/v1`
- `GET /api/v1/{resource}?limit=20`
- `GET /api/v1/{resource}/{run_id}`

## Private Dashboard

- `app/dashboard.py` — HTTP API client, GET-only WSGI routes and server-side HTML rendering.
- `scripts/run_dashboard.py` — local/private dashboard server entry point.
- `docs/DASHBOARD.md` — operating and safety instructions.

The dashboard reads `/health` and `/api/v1` over HTTP only. It has no direct database, Dhan or execution dependency.

## Alert Service

- `services/alert_models.py` — normalized alert candidates, persisted events and run results.
- `services/alert_repository.py` — persisted source reads, event deduplication and delivery audit records.
- `services/alert_service.py` — generation, channel isolation, successful-delivery suppression and failed-delivery retry policy.
- `services/alert_channels.py` — console and configurable private-webhook adapters.
- `scripts/generate_alerts.py` — operational entry point.

Alert sources are limited to persisted signals, risk decisions and pipeline health. See `docs/ALERTS.md`.

## AI Copilot

- `services/copilot_api_client.py` — GET-only client for the stable read API.
- `services/copilot_evidence.py` — question routing, symbol filtering and citation construction.
- `services/copilot_models.py` — validated requests, evidence and answers.
- `services/copilot_service.py` — safety refusal, grounding, fallback and verified-source attachment.
- `services/copilot_provider.py` — optional provider interface and OpenAI Responses adapter.
- `scripts/ask_copilot.py` — private command-line research surface.

The default provider is deterministic and local. Model providers have no platform tools or execution authority. See `docs/COPILOT.md`.

## Paper Trading

- `services/paper_trading_models.py` — validated requests and attributed order, fill and position models.
- `services/paper_trading_repository.py` — persisted signal/mark reads and transactional paper-state persistence.
- `services/paper_trading_service.py` — deterministic entry, mark, close, slippage, cost, P&L and transition policy.
- `scripts/paper_trade.py` — open, mark, close and status commands.

Paper trading has no Dhan or broker-order dependency. See `docs/PAPER_TRADING.md`.
