# Read-Only API

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
