# Private Read-Only Dashboard

## Start locally

From the repository root and active virtual environment, start the two processes in separate terminals:

```bash
python -m scripts.run_read_api
```

```bash
python -m scripts.run_dashboard
```

Open `http://127.0.0.1:8081`.

Both services bind to loopback by default. The dashboard port defaults to `8081`, the API defaults to `8080`, and no external network access is required.

## Configuration

```bash
python -m scripts.run_dashboard \
  --host 127.0.0.1 \
  --port 8081 \
  --api-base-url http://127.0.0.1:8080 \
  --api-timeout 5
```

## Screens

- Overview with API and database readiness.
- Recent ranking runs and ranked underlyings.
- Contract selections with ranking lineage.
- Risk approvals, rejections, sizing and exposure.
- Signals with confidence, rationale, entry reference and maximum loss.
- Ordered replay timelines.
- Backtest summaries and trade results.

Each resource list links to its run detail. Valid empty collections display a stable empty state. Unavailable API responses, invalid response data and missing runs display non-destructive error or not-found states.

## Safety boundary

- Dashboard data is fetched only through HTTP GET requests to `/health` and `/api/v1`.
- Dashboard code has no PostgreSQL repository or Dhan client dependency.
- The dashboard has no forms, write routes, calculations, order execution or broker access.
- Responses disable caching and framing and use a restrictive content security policy.
