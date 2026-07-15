# Services

## Version 3 research baseline

`ResearchBaselineRepository` performs one bounded SELECT projection over Version
2 Feature, Outcome, Ranking and Opportunity evidence. `ResearchBaselineService`
owns the checksummed `v3-research-contract-v1`, fixed periods, registered baseline
selection and null-safe metrics. `scripts.benchmark_recommendations` emits the
deterministic JSON report. None can collect data, persist state, call a model or
generate a recommendation.

## AI Trading Analyst

`TradingAnalystEvidenceService` assembles complete, versioned evidence through
existing application services. `TradingAnalystService` owns request validation,
pre-retrieval refusal, local synthesis, optional provider fallback and
application-attached citations. It performs no persistence or financial policy.

## Version 2 release readiness

The SELECT-only readiness repository audits Feature Store, Outcome, Similarity,
Opportunity, Event and Analyst grounding lineage in addition to Version 1
invariants. Similarity and event checks explicitly detect future-data leakage.

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

## Release Readiness

- `services/release_readiness_models.py` — migration evidence, audit metrics,
  deterministic statuses and the aggregate report.
- `services/release_readiness_repository.py` — SELECT-only PostgreSQL evidence.
- `services/release_readiness_service.py` — migration comparison and release
  invariant policy.
- `scripts/verify_release.py` — console report with success/failure exit status.

PASS means evidence satisfies the invariant. FAIL blocks release. SKIP is limited
to optional persisted datasets with no records. The service does not run migrations,
perform cleanup, call Dhan or invoke any product workflow.

## Similarity Engine

- `services/similarity_repository.py` — persisted Feature/Outcome reads and
  auditable run/match persistence.
- `services/similarity_service.py` — historical-only scaling, weighted distance,
  deterministic ranking, evidence statistics and outcome attachment policy.
- `scripts/materialize_similarity_run.py` — explicit operator materialization.

No similarity service calls Dhan, generates recommendations or changes source
market records. See `docs/SIMILARITY_ENGINE.md`.

## Trade Opportunity Engine

- `services/trade_opportunity_repository.py` — persisted similarity evidence
  reads and Opportunity Store persistence.
- `services/trade_opportunity_service.py` — evidence eligibility, deterministic
  zones, expected value, win rate, evidence quality, risk/reward and ranking.
- `scripts/materialize_trade_opportunities.py` — explicit offline materializer.

The service has no AI, broker, Dhan, alert or paper-trading dependency. See
`docs/TRADE_OPPORTUNITY_ENGINE.md`.

## News and Event Intelligence

- `services/news_event_provider.py` — provider protocol and bounded local JSON adapter.
- `services/news_event_repository.py` — event and derived-context persistence/reads.
- `services/news_event_service.py` — validation, sanitization, identity, explicit
  relevance, leakage prevention and context-only policy.
- `scripts/import_news_events.py`, `scripts/link_historical_events.py` and
  `scripts/materialize_opportunity_events.py` — offline operator workflow.

No service calls an external provider, AI, Dhan, alerts or execution. See
`docs/NEWS_EVENT_INTELLIGENCE.md`.

## Version 3 Provider Strategy

V3.0.5 adds documentation only. It defines future canonical interfaces for
instrument masters, bars, option chains, depth, actions, events and news, plus
source priority, failover, deduplication, revisions, conflicts, checksums, raw
manifests, licensing and retention metadata. No executable adapter or service has
been added. Existing Dhan collectors and the bounded local news-event provider are
unchanged. See `docs/V3_DATA_PROVIDER_STRATEGY.md`.

## Version 3 Historical Data Foundation

- `historical_data_models.py` defines frozen source, retention, raw, instrument,
  mapping, bar, action, dataset and result contracts.
- `historical_data_provider.py` defines the adapter protocol and bounded
  local-JSON implementation with no network or credentials.
- `historical_data_service.py` owns validation, fail-closed licensing, exact raw
  and canonical checksums, deterministic IDs and natural-key preparation.
- `historical_data_repository.py` atomically persists immutable raw payloads,
  manifests, canonical revisions, deduplication and conflict quarantine.

No command, live provider adapter, scheduler or continuous collector is included.
See `docs/HISTORICAL_DATA_FOUNDATION.md`.

## Version 3 Continuous Market Collection

`continuous_collection_models`, `continuous_collection_policy`,
`continuous_collection_provider`, `continuous_collection_repository` and
`continuous_collection_service` define session-aware work, bounded claims and
retries, fixture ingestion, gaps, repairs, quota state and health.
`continuous_collection_scheduler` reuses the existing scheduler lock pattern.
Only the bounded local fixture provider is implemented.

## Version 3 Outcome Engine V2

`outcome_v2_models` defines immutable horizons and policies.
`outcome_v2_repository` performs point-in-time canonical bar/action reads and
atomic outcome/path persistence. `outcome_v2_service` owns deterministic horizon,
barrier, missingness, cost, MFE/MAE, drawdown and volatility policy.
`materialize_historical_outcomes_v2` is the offline idempotent command. No current
Similarity, Opportunity, Analyst or recommendation service imports it.

## Version 3 Feature Store V2

`feature_store_v2_models` defines versioned definitions, schemas, anchors and
results. `feature_store_v2_repository` performs point-in-time revision reads and
atomic immutable persistence. `feature_store_v2_service` computes deterministic
features, explicit missingness, quality and lineage. The offline command is
`materialize_feature_store_v2`; no provider or current consumer is invoked.

## Version 3 Similarity Engine V2

`similarity_v2_models` freezes transparent policies, `similarity_v2_repository`
owns point-in-time Feature/Outcome reads and immutable persistence, and
`similarity_v2_service` owns normalization, filtering, distance, ranking,
explainability, quality and abstention. `materialize_similarity_v2` is offline.

`opportunity_v2_models`, `opportunity_v2_repository` and
`opportunity_v2_service` freeze strategy policy, select exact contracts, calculate
option-path provisional fields, enforce abstention and persist immutable lineage.
`calibration_v2_*` fits transparent bins, calculates deterministic uncertainty
and evaluates eligibility without execution side effects.
`live_validation_*` freezes evaluations, reconstructs canonical shadow paths,
calculates outcomes/reports/drift and appends suspensions without modifying models.
`research_governance_*` owns offline registration, paired replay, comparison,
approval gates, role assignments, rollback plans and immutable audit history.
