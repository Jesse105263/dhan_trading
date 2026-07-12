# Private Alerts

## Purpose

Alerts are generated only from committed platform records. Supported source types are:

- `SIGNAL` from `option_signals`.
- `RISK_DECISION` from `option_risk_assessments`, including approvals and rejections.
- `PIPELINE_HEALTH` from failed pipeline runs or runs with persisted failure records.

Alert generation does not call Dhan, recalculate analytics, modify source records or place orders.

## Run locally

Apply migrations first:

```bash
python -m services.migration_runner
```

Generate all current alerts on the private console channel:

```bash
python -m scripts.generate_alerts
```

Select sources and channels explicitly:

```bash
python -m scripts.generate_alerts \
  --source signal \
  --source risk \
  --source pipeline \
  --channel console \
  --limit 100
```

Deliver to a configured private webhook:

```bash
python -m scripts.generate_alerts \
  --channel webhook \
  --webhook-url http://127.0.0.1:9000/alerts
```

Webhook delivery is outbound only and sends structured JSON. It is not a broker endpoint and has no execution capability.

## Deduplication and retry behavior

`alert_events` has one immutable event per source type and source ID. Reprocessing reuses that event rather than creating a duplicate. A channel with a successful delivery is skipped on later runs. A failed channel remains eligible for retry.

Every delivery is recorded in `alert_delivery_attempts` with a channel, attempt number, status, timestamps and sanitized failure message. Delivery failures are reported by the command, persisted for audit, and do not roll back the alert event or affect other channels.

## Severity policy

- Signals: `INFO`.
- Approved risk decisions: `INFO`.
- Rejected risk decisions: `WARNING`.
- Completed pipeline runs containing failures: `WARNING`.
- Failed pipeline runs: `CRITICAL`.
