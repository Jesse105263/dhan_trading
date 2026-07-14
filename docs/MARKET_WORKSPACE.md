# Version 2 Market Workspace

V2.0.5 delivers a persisted Market Overview, dense Opportunity Scanner and minimal
opportunity detail for one private owner. It never labels data live, predicts profit,
triggers a pipeline or exposes a trading command.

## Read API

- `GET /api/v2` lists V2 read resources.
- `GET /api/v2/overview` returns database health, latest successful option-chain
  run, latest ranking run, downstream counts and five recent sanitized failures.
- `GET /api/v2/opportunities` returns the latest ranking run's items.
- `GET /api/v2/opportunities/{ranking_id}` returns linked decision lineage.

`/api/v1` is unchanged. V2 handlers use `MarketWorkspaceService` and the SELECT-only
`MarketWorkspaceRepository` within the existing standard-library WSGI application.

## Filters, Sorting and Bounds

Optional filters are case-insensitive `symbol`, exact `expiry`, `minimum_score`
from 0 to 1, `freshness` (`current`, `aging`, `stale`), and boolean `selection`,
`risk_approved` and `signal`. `limit` defaults to 25 and is bounded 1–100; `offset`
is bounded 0–10,000. Sort fields are `rank`, `score`, `captured_at` and `symbol`;
direction is `asc` or `desc`. Default order is rank ascending with ranking ID as
the final tie-break.

Invalid input returns `400 invalid_query`, missing detail returns `404 not_found`,
and database failures return `503 database_unavailable`.

## Freshness and Lineage

- `current`: at most 15 minutes old.
- `aging`: over 15 and at most 60 minutes old.
- `stale`: over 60 minutes old.
- `unavailable`: no source timestamp.

Overview uses latest successful option-run completion; opportunities use
`source_captured_at`. The timestamp is displayed. Availability joins by exact
`ranking_id`, distinguishing ranking, selection, approved risk and signal stages.
Empty latest runs and missing downstream stages are valid explicit states.

## Local Use and Safety

Run `python -m scripts.run_read_api` and `npm run dev` from `frontend/` in separate
terminals, using the proxy configuration in `docs/FRONTEND.md`. Endpoints are
GET-only and cannot call Dhan, run analytics, deliver alerts, create paper positions
or place orders. The browser cannot access PostgreSQL or Dhan.
