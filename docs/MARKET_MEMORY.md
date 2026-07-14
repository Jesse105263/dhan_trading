# Market Memory and Feature Store

## Purpose

V2.0.7 establishes a queryable historical-evidence layer for future statistically
grounded research. It does not generate a trade, recommendation, entry, stop,
target, confidence estimate, expected value or win rate.

## Storage Decision

The feature store uses the repository's existing immutable normalized records as
its canonical storage. `option_chain_analytics`, `option_analytics_changes`,
`option_rankings`, `option_contract_selections`, `option_risk_assessments`,
`option_signals`, `scanner_snapshots` and `market_features` already persist the
observations and their lineage. A second copy would create synchronization and
provenance risk, so V2.0.7 adds a SELECT-only repository and deterministic query
service rather than migration `018`.

The canonical option snapshot identifier is `option_chain_analytics.analytics_id`.
Snapshots are ordered by `source_captured_at DESC, analytics_id DESC`. Exact
analytics-change lineage is joined by foreign key, never guessed by time
proximity. If an analytics snapshot participates in multiple ranking runs, the
latest persisted ranking is selected deterministically by ranking-run calculation
time and ID.

## Supported Features

The API allow-list contains persisted option analytics and linked ranking values:

- spot, ATM strike/distance, ATM call/put price and straddle cost;
- total/nearby call and put OI and PCR;
- ATM and nearby call/put/mean IV;
- call/put OI wall strikes and values;
- price and liquidity coverage;
- rank position, total score, and liquidity/activity/volatility/directional scores.

Existing equity `market_features` remain the canonical persisted equity feature
store. Selection, risk and signal histories remain queryable through the bounded
symbol-intelligence projection documented in `docs/SYMBOL_WORKSPACE.md`; their
foreign keys retain exact downstream lineage from a ranking snapshot. IV
percentile, historical volatility, IV/HV ratio, Greeks, standalone risk
score, and time to expiry are not persisted by current pipelines and are not
invented or calculated in this milestone.

## Read API

All routes are GET-only, bounded to 200 observations, and return structured errors:

- `GET /api/v2/memory?symbol=...&expiry=...&from=...&to=...&limit=...`
- `GET /api/v2/memory/latest?symbol=...&expiry=...`
- `GET /api/v2/memory/previous?symbol=...&expiry=...`
- `GET /api/v2/memory/snapshots/{analytics_id}`
- `GET /api/v2/memory/features/{feature}?symbol=...&expiry=...`
- `GET /api/v2/memory/compare?previous={analytics_id}&current={analytics_id}`

`symbol` is required. Dates use ISO date syntax and range boundaries use ISO
timestamps. Comparison accepts any two canonical snapshots, orders its operands by
capture time, and returns only persisted context/features whose values differ. Each snapshot
includes source, analytics, change and ranking lineage identifiers plus the V2
presentation freshness state.

## Workspace

`/memory` provides symbol/expiry filtering, a bounded chronological table, a
lightweight SVG feature-evolution trace and an accessible two-snapshot comparison.
Loading, empty, database/API error and stale states remain explicit. The browser
does not calculate market analytics; SVG coordinates are presentation only.

## Safety and Operations

The repository and service execute SELECT statements only. There are no collectors,
pipeline triggers, writes, Dhan calls, alerts, paper commands, model calls, or live
execution paths. `/api/v1` is unchanged and no database migration or dependency is
introduced.

Local verification uses the standard WSGI server and Vite frontend. Safe read-only
checks include the V2 index, an empty or persisted memory query, invalid filter
handling and a missing snapshot 404.
