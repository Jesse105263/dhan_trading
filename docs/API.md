# Read-Only API

V2.0.5 adds GET-only `/api/v2`, `/api/v2/overview`, `/api/v2/opportunities`
and `/api/v2/opportunities/{ranking_id}` without changing the Version 1 contract.
See `docs/MARKET_WORKSPACE.md` for filters, sorting, bounds, freshness and errors.

V2.0.6 adds bounded `GET /api/v2/symbols` search and expiry-aware
`GET /api/v2/symbols/{symbol}` intelligence. See `docs/SYMBOL_WORKSPACE.md`.

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
