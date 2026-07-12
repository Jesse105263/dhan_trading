# Dhan Trading Platform Architecture

## Vision

Build a professional-grade market intelligence and options trading platform capable of:

- Real-time market monitoring
- Historical analytics
- AI-assisted research
- Strategy development
- Trade execution support
- Institutional-grade scalability

---

# High Level Architecture

                    ┌────────────────────────┐
                    │     Dhan APIs          │
                    └──────────┬─────────────┘
                               │
                    ┌──────────▼─────────────┐
                    │  Market Collectors     │
                    └──────────┬─────────────┘
                               │
                    ┌──────────▼─────────────┐
                    │      PostgreSQL        │
                    └──────────┬─────────────┘
                               │
                    ┌──────────▼─────────────┐
                    │        Redis           │
                    └──────────┬─────────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
        Signal Engine                 Dashboard/API
                │                             │
                └──────────────┬──────────────┘
                               │
                        Telegram Alerts
                               │
                        AI Research Layer
                               │
                        GPT / Claude APIs

---

## Design Principles

- PostgreSQL is the source of truth.
- Redis stores live data only.
- CSV files are temporary.
- Docker manages infrastructure.
- Every service is independently replaceable.
- AI never participates in live trade execution.

---

## Deployment Strategy

Phase 1

MacBook Development

↓

Phase 2

Cloud VPS

↓

Phase 3

Production Server

↓

Phase 4

Multi-machine architecture
---

## Expiry Selection Boundary

`derivative_contracts` is the persistent source of truth for available derivative expiries.

```text
derivative_contracts
        │
        ▼
ExpiryRepository
(database queries only)
        │
        ▼
ExpiryService
(selection and validation policy)
        │
        ├── Option-chain collector
        ├── Contract selection
        ├── Risk engine
        └── Strategy services
```

No downstream component may independently sort, choose or validate expiries. This keeps collection, strategy and risk behavior deterministic and consistent.

## Option-Chain Collection Boundary

`OptionChainCollector` orchestrates one collection. It resolves the underlying through `OptionChainRepository`, delegates expiry policy exclusively to `ExpiryService`, fetches through `DhanOptionChainClient`, validates and normalizes the response, and transactionally persists quotes and run completion. Downstream code must not select expiries independently.

## Option Analytics Boundary

`OptionAnalyticsService` is the only component that derives analytics from a persisted option-chain run. It does not call Dhan and does not select expiries. `OptionAnalyticsRepository` owns completed-run reads and idempotent analytics persistence. Every analytics row retains immutable lineage to exactly one `option_chain_runs.run_id`.

## Option Data Operational Pipeline

The option data platform runs in a dedicated pipeline that does not modify the production equity pipeline. `OptionCollectionStage` processes configured underlyings with bounded retry and throttling. `OptionAnalyticsStage` consumes only successful collection results and preserves source-run lineage through `option_chain_analytics.source_run_id`. Per-underlying failures are sanitized and persisted without aborting successful symbols. The existing scheduler lock repository provides one-shot overlap protection under a dedicated option-pipeline lock name.

## Option Analytics History Boundary

`OptionAnalyticsHistoryRepository` owns ordered analytics retrieval, predecessor selection and change persistence. `OptionAnalyticsHistoryService` owns comparability validation and deterministic change calculation. Downstream ranking and signal components must consume persisted change records rather than reimplement time-series comparison logic.

## Ranking Engine

`OptionRankingService` ranks the latest comparable analytics/change snapshots. `OptionRankingRepository` owns candidate reads and ranking persistence. Every result stores analytics and change lineage plus component explanations.

## Contract selection boundary

The contract-selection layer is downstream of ranking and upstream of risk. It reads only persisted ranking and source-chain records, applies deterministic tradeability constraints, and persists explainable selections with full lineage.

## Option Risk Engine

`OptionRiskService` is the only component allowed to approve and size selected option contracts. It treats premium paid for long options as maximum loss and applies portfolio-aware limits before signal generation. `OptionRiskRepository` reads persisted contract selections and stores immutable risk runs and per-contract decisions with full lineage.

## Signal Engine

`OptionSignalService` consumes only persisted, approved option-risk assessments. It generates auditable buy-to-open signal records with deterministic direction, confidence, strategy context, position size and complete upstream lineage. It has no broker execution capability.

## Market Replay

`MarketReplayService` reconstructs an immutable ordered timeline exclusively from persisted option-chain, analytics, ranking, selection, risk and signal records. It never calls Dhan and never places orders.

### Option Backtesting
`OptionBacktestService` evaluates persisted signals only against later completed option-chain snapshots. It never calls Dhan and never places orders. `OptionBacktestRepository` owns signal/mark reads and transactional result persistence.

## Read-Only Application API

`app.read_api.ReadOnlyApi` is the HTTP boundary for persisted product data. It is GET-only, versioned under `/api/v1`, and delegates all database access to `ReadApiRepository`. The API exposes run summaries and run details for rankings, selections, risk assessments, signals, market replays and backtests. It performs no calculations, writes or broker calls.

## Private Read-Only Dashboard

`app.dashboard.DashboardApplication` is a separate WSGI presentation boundary. `DashboardApiClient` obtains health, list and detail payloads exclusively through HTTP GET requests to the stable read API. The dashboard never imports a repository, queries PostgreSQL, calls Dhan or exposes write behavior. It binds to loopback by default and renders server-side HTML with explicit empty, error and not-found states.
