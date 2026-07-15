# Dhan Trading Platform Architecture

V3.0 adds a read-only research boundary above persisted Version 2 evidence. A
repository selects point-in-time Feature, Outcome, Ranking and Opportunity facts;
a deterministic service applies a checksummed research contract and emits baseline
metrics. It does not modify the intelligence chain or expose an API. Later Version
3 work must version data, features, labels, models and calibration against this
contract rather than redesign completed Version 2 components.

News and Event Intelligence follows the repository/service boundary: approved
local adapters feed validated events to PostgreSQL, deterministic services
materialize point-in-time links, and GET-only APIs expose context. Read requests
never fetch news externally and no event path reaches execution.

The AI Trading Analyst is an application-layer evidence consumer. It assembles a
versioned packet from existing V2 services before local or optional isolated model
synthesis. The application attaches citations; providers receive no tools or
database, broker, alert, Dhan or execution access.

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

## Alert Boundary

`AlertRepository` reads only persisted signals, risk assessments, pipeline runs and pipeline failures, then owns alert-event and delivery-attempt persistence. `AlertService` owns source validation, deduplication flow, channel isolation and retry behavior. Console and generic private-webhook channels are replaceable delivery adapters. Alert generation never calls Dhan, recalculates analytics, mutates source records or places orders.

```text
Persisted signals / risk decisions / pipeline health
                         │
                         ▼
                   AlertRepository
                         │
                         ▼
                    AlertService
                         │
                 ┌───────┴────────┐
                 ▼                ▼
           Console channel   Private webhook
                         │
                         ▼
              Delivery-attempt audit
```

## AI Copilot Boundary

`CopilotEvidenceService` selects relevant read-API resources and constructs immutable citation records from run and item lineage. `CopilotService` enforces execution refusal, insufficient-evidence behavior, verified source attachment and model-failure fallback. The default local provider renders deterministic evidence summaries; the optional `OpenAIResponsesProvider` performs natural-language synthesis without tools or write capabilities.

```text
Question
   │
   ▼
Execution boundary ── refusal
   │ allowed research
   ▼
/api/v1 GET evidence
   │
   ▼
Verified lineage records
   │
   ├── Local synthesis
   └── Optional model synthesis
   │
   ▼
Answer + application-attached citations
```

The model never retrieves data itself and cannot access PostgreSQL, Dhan, alerts, orders or execution services.

## Paper-Trading Boundary

`PaperTradingRepository` reads persisted signals and completed option-chain marks and owns isolated paper-state persistence. `PaperTradingService` applies deterministic entry, marking, close, slippage, cost, P&L and transition policy. Paper tables preserve complete source lineage but cannot submit or promote an order to a broker.

```text
Persisted approved signal + persisted option-chain mark
                         │
                         ▼
                PaperTradingService
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
        Paper order    Paper fill   Paper position
                                      │
                                      ▼
                              Ordered audit events
```

The boundary has no Dhan client, broker-order adapter or live-order state transition.

## Release Readiness Boundary

`ReleaseReadinessRepository` performs SELECT-only inspection of migration metadata,
persisted lineage, operational run state and database object names.
`ReleaseReadinessService` compares that evidence with the immutable filesystem
migration manifest and emits deterministic PASS, FAIL and SKIP results.
`scripts.verify_release` is an operator-facing report and never runs migrations,
calls Dhan, delivers alerts, invokes a model or changes paper state.

```text
Migration files + committed PostgreSQL state
                    │
                    ▼
        ReleaseReadinessRepository
             (SELECT statements only)
                    │
                    ▼
          ReleaseReadinessService
                    │
                    ▼
          PASS / FAIL / SKIP report
```

Backup and restore remain explicit operator procedures. Recovery verification must
target a newly created isolated database and must never replace the normal
PostgreSQL database.

## Version 3 Provider-Neutral Data Boundary

V3.0.5 defines, but does not implement, a raw-to-canonical boundary for instrument
masters, underlying/futures/option bars, option-chain and depth snapshots,
corporate actions, events and news. Provider payloads must remain immutable and
checksummed; temporal symbol mappings connect provider IDs to stable canonical
instrument IDs. Canonical revisions preserve availability time and source lineage.

DhanHQ is selected for historical acquisition and live backup, TrueData for
continuous collection, NSE/BSE for authoritative venue facts, and RBI/MoSPI for
macro facts, all subject to their licensing gates. Feature, Outcome, Similarity
and research layers must not consume provider payloads directly. Unknown retention
or model-use permission fails closed. See `docs/V3_DATA_PROVIDER_STRATEGY.md`.

V3.1 implements this boundary in migration `023`. Exact raw bytes flow through a
provider-neutral adapter into a single transactional repository; manifests retain
raw and canonical checksums. Stable instrument UUIDs and temporal provider mappings
separate identity from tickers/security IDs. Bars and corporate actions append
revisions with availability timestamps; differing cross-source bars quarantine
without replacing accepted state. The only adapter is bounded local JSON and has
no network or credential capability. See `docs/HISTORICAL_DATA_FOUNDATION.md`.

## Version 3 Continuous Collection Boundary

V3.2 adds deterministic session policy and a restartable PostgreSQL work queue in
migration `024`. Scheduler locks and atomic claims prevent overlap; immutable
attempts retain partial success, retries and failures. Successful bytes enter V3.1
unchanged. Gaps create idempotent repair work and late/conflicting records retain
V3.1 revision and quarantine semantics. Only a local fixture provider exists;
Dhan production collection is not connected or changed.

## Version 3 Outcome Engine V2 Boundary

Outcome V2 is a new immutable consumer of V3.1 canonical bar/action revisions.
It selects evidence as of an explicit cutoff, reconstructs ordered underlying or
option paths, and persists versioned labels plus exact manifests. The existing V2
Outcome Store remains the source for current Similarity and Opportunity logic;
V3.3 adds no recommendation integration.

## Version 3 Feature Store V2 Boundary

V3.4 reads only point-in-time V3.1 canonical bars and persists isolated immutable
feature evidence. It does not replace the V2 Feature Store or feed Similarity,
Opportunity, Analyst or recommendation services. Outcome V2 compatibility is
declared metadata, never a predictive input.

## Version 3 Similarity Engine V2 Boundary

V3.5 reads immutable Feature Store V2 vectors, ranks only pre-cutoff candidates,
then attaches Outcome V2 evidence completed before the query observation. Its
new tables and command are isolated from V2 Similarity, Opportunity, Analyst and
recommendation paths.

## Version 3 Opportunity Engine V2 Boundary

V3.6 persists isolated provisional research over exact Feature/Similarity/Outcome
lineage. It has no connection to V2 Opportunity, Analyst, recommendation,
collection, broker or execution services.
