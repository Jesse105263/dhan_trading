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

## Version 3.3 — Outcome Engine V2

V3.3 preserves the complete V2 API and `historical_outcomes` contract above.
Migration `025` adds a separate immutable canonical outcome store so Similarity,
Trade Opportunity and Analyst behavior cannot change implicitly.

### Inputs and point-in-time policy

Outcome V2 reads only accepted canonical `historical_bar_revisions`, stable
instrument identities and confirmed/revised corporate actions. Anchor and path
queries select the latest same-natural-key revision whose `available_at` is at or
before the explicit materialization `as_of`; a later correction cannot leak into
an earlier run. Raw manifests remain the evidence source for every anchor,
terminal and path bar.

Both equities/indices and options are supported when canonical bars exist.
Futures remain canonical instruments but are not labelled as underlying or option
subjects in this model. No proxy option price, interpolation or fill is invented.

### Horizons, states and path metrics

Policies are immutable under a model version and configure duration, trading-
session and expiry horizons. The default model registers 30-minute, one-session,
five-session and through-expiry horizons. A horizon completes only when its exact
duration, required session or expiry observation is present.

States are `COMPLETE`, `UNKNOWN`, `INSUFFICIENT` and `AMBIGUOUS`. Missing entry,
horizon or expiry evidence remains `UNKNOWN`; too few path observations or an
unadjusted price-altering corporate action is `INSUFFICIENT`; a bar touching both
target and stop without intrabar ordering is `AMBIGUOUS`. Only `COMPLETE` records
receive gross/net return, MFE, MAE, maximum drawdown, realized volatility and
volatility-adjusted return.

Configured round-trip costs reduce gross returns deterministically. Target/stop
barriers are optional. The service never guesses first-touch ordering. Aggregate
statistics calculate expectancy as mean complete net return and payoff ratio as
average positive net return divided by absolute average negative net return;
unsupported populations return null.

### Persistence and operation

`outcome_model_versions_v2` freezes policy/checksum identity,
`outcome_materialization_runs_v2` records the point-in-time run population,
`historical_outcomes_v2` stores one deterministic anchor/version/horizon label,
and `historical_outcome_path_v2` stores its ordered exact bar/manifests. Outcomes
and paths reject update/delete. UUIDv5 and unique constraints make reruns
idempotent.

```bash
python -m services.migration_runner
python -m scripts.materialize_historical_outcomes_v2 --as-of 2026-07-16T00:00:00
```

The command is offline and provider-free. The current local historical foundation
contains no licensed market population, so an empty run is valid and makes no
coverage or statistical-reliability claim.

## V3.4 compatibility boundary

Feature Store V2 declares compatibility with `canonical-path-outcome-v2`, but
Outcome V2 labels and metrics are never feature inputs. This prevents label or
future-path leakage. Neither store changes the existing V2 Similarity consumer.

## V3.5 similarity consumer

Outcome V2 is attached only after analogue ranking. Only complete outcomes whose
terminal timestamp is no later than the query observation are eligible; outcomes
never affect feature selection, normalization, distance or rank.

V3.6 uses complete option outcomes for premium-path MFE, MAE and net returns.
Unknown or underlying-only paths cannot support option entry, stop or targets.
