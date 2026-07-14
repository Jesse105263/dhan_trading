# Historical Outcome Engine

V2.1.4 audited 9 persisted outcomes with zero lineage violations. None is an
expiry-classified outcome, so statistically reliable recommendations are unsupported.

## Purpose

V2.0.9 persists objective ground truth describing what happened after each Feature
Store observation. Similarity and opportunity engines must consume these records;
they must not recompute or reinterpret outcomes independently.

## Model

Model `underlying-through-expiry-v1` measures the persisted underlying spot from a
source vector through later vectors with the same symbol and expiry, capped at the
expiry date. It records:

- forward and closing percentage return at the latest available observation;
- maximum favourable and adverse percentage excursion (MFE and MAE);
- peak gain and loss in underlying spot units;
- holding duration and future-observation count;
- expiry return and win/loss only when an expiry-date observation exists.

Outcomes have three states:

- `NO_FUTURE_DATA`: no later priced observation; all outcome metrics are null;
- `PARTIAL`: later data supports interim return/excursions, but expiry outcome and
  win/loss remain null;
- `EXPIRY_COMPLETE`: an expiry-date observation supports final return and win/loss.

Zero return is classified as not won. No interpolation, estimate, prediction,
option-price proxy or fabricated expiry mark is used.

## Persistence and Lineage

Migration `019_historical_outcomes.sql` adds one versioned outcome per Feature
Store vector. Deterministic UUIDv5 identity uses the model version and vector ID.
Every record retains feature vector, analytics, optional ranking, and terminal
vector lineage. Re-materialization updates the same outcome and never duplicates it.

## Materialization

```bash
python -m services.migration_runner
python -m scripts.materialize_historical_outcomes
```

The offline command scans vectors in deterministic bounded batches and is
restartable. `--limit N` is available for focused verification. It reads persisted
features only, calls no collector or external service, and generates no trade.

## Read API

- `GET /api/v2/outcomes`
- `GET /api/v2/outcomes/{outcome_id}`
- `GET /api/v2/outcomes/statistics`
- `GET /api/v2/outcomes/history`

Filters are `symbol`, `expiry`, `from`, `to`, `outcome_type`, and bounded `limit`.
History is chronological; the normal list is reverse chronological. Statistics
are calculated only from stored outcomes: classified win rate, average and median
closing return, average MFE/MAE, and best/worst closing return. Empty or incomplete
populations return null statistics rather than invented values.

## Limitations

The current repository persists option-chain observations rather than continuous
intraday bars. Excursions therefore describe the observed snapshot path, not an
unobserved tick-level path. Current outcomes measure underlying spot because every
Feature Store vector has that objective value; they do not claim selected-contract
P&L. Sparse histories naturally remain partial or unavailable.

No recommendation, entry, stop, target, expected value, confidence, AI reasoning,
broker request or execution capability exists in this milestone.
