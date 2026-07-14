# Read-Only API

V2.0.5 adds GET-only `/api/v2`, `/api/v2/overview`, `/api/v2/opportunities`
and `/api/v2/opportunities/{ranking_id}` without changing the Version 1 contract.
See `docs/MARKET_WORKSPACE.md` for filters, sorting, bounds, freshness and errors.

V2.0.6 adds bounded `GET /api/v2/symbols` search and expiry-aware
`GET /api/v2/symbols/{symbol}` intelligence. See `docs/SYMBOL_WORKSPACE.md`.

V2.0.7 adds bounded `GET /api/v2/memory`, `/latest`, `/previous`, snapshot
detail, allow-listed feature history and exact comparison. See
`docs/MARKET_MEMORY.md`.

V2.0.8 adds GET-only feature definitions, bounded vector lists and vector detail
under `/api/v2/features`. See `docs/FEATURE_STORE.md`.

V2.0.9 adds bounded outcome lists/detail, chronological history and persisted-only
statistics under `/api/v2/outcomes`. See `docs/HISTORICAL_OUTCOME_ENGINE.md`.

V2.1.0 adds similarity model metadata, non-mutating analysis and persisted-run
reads under `/api/v2/similarity`. Analysis requires `vector_id`; supports bounded
limit, symbol/expiry restrictions and an earlier historical cutoff. Responses
include exact lineage, diagnostics, persisted outcomes and explicit evidence
state. See `docs/SIMILARITY_ENGINE.md`. `/api/v1` remains unchanged.

V2.1.1 adds bounded persisted opportunity lists and exact evidence detail under
`/api/v2/trade-opportunities`. These routes are distinct from the existing ranking
projection at `/api/v2/opportunities`. See `docs/TRADE_OPPORTUNITY_ENGINE.md`.

Base URL: `http://127.0.0.1:8080`

## Contract

All endpoints are read-only. Only `GET` is accepted. Responses use JSON and structured errors.

### Health

`GET /health`

### API index

`GET /api/v1`

### Latest runs

`GET /api/v1/{resource}?limit=20`

Supported resources:

- `rankings`
- `selections`
- `risk`
- `signals`
- `replays`
- `backtests`

`limit` defaults to 20 and must be between 1 and 100.

### Run detail

`GET /api/v1/{resource}/{run_id}`

Returns the selected run and its ordered child records in `data.items`.

## Safety boundary

The API cannot place orders, invoke Dhan, modify persisted records or trigger calculations.

## Dashboard consumer

The private dashboard is an HTTP consumer of this contract. It does not import the read repository or access PostgreSQL. Start the API before the dashboard and keep the API reachable at the dashboard's configured `--api-base-url`.

## Copilot consumer

The private AI Copilot retrieves evidence only through the list and detail routes in this contract. It does not import the read repository, query PostgreSQL, invoke Dhan or expose execution tools.
