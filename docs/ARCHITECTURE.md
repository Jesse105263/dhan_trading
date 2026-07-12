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
