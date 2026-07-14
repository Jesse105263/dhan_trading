# Version 2 Feature Store

## Purpose

V2.0.8 persists versioned numeric feature vectors for every canonical option
observation so the Historical Outcome and Similarity engines can consume one
stable, point-in-time input contract. It adds no AI, recommendation or execution
behavior.

## Schema

Migration `018_feature_store.sql` adds:

- `feature_store_vectors`: deterministic vector identity, source lineage, symbol,
  expiry, observation time, schema version and quality metadata;
- `feature_store_values`: normalized numeric values with feature group and exact
  source relation/field.

`analytics_id` plus `schema_version` is unique. Re-materialization is idempotent
and refreshes only the derived cache for that canonical observation. Deleting a
canonical analytics record cascades its derived vector. Source change/ranking IDs
remain explicit and are never inferred by approximate timestamps.

## Feature Contract

Schema `option-observation-v1` contains 56 definitions:

- 32 fields already persisted by `option_chain_analytics`;
- 17 fields already persisted by `option_analytics_changes`;
- six fields already persisted by `option_rankings`;
- `time_to_expiry_days`, deterministically derived from persisted expiry and
  source capture date.

Nullable source data remains null. `PARTIAL` records report the exact missing
feature count; no imputation occurs. Clock-relative freshness is excluded because
it changes without a new observation. IV percentile, historical volatility,
IV/HV ratio and Greeks remain excluded because current pipelines do not persist
the inputs required to calculate them reliably.

## Materialization

After applying migrations, materialize all canonical observations in bounded,
ordered batches:

```bash
python -m services.migration_runner
python -m scripts.materialize_feature_store
```

Use `--limit N` only for focused verification. The command calls no collector,
Dhan API, model, alert or trading service. It is the only write path added in this
milestone; HTTP remains GET-only.

## Read API

- `GET /api/v2/features/definitions`
- `GET /api/v2/features?symbol=RELIANCE&expiry=YYYY-MM-DD&limit=50`
- `GET /api/v2/features/{vector_id}`

Lists are bounded to 200, ordered by observation timestamp and deterministic ID,
and include the complete numeric vector and lineage metadata. `/api/v1` is
unchanged.

## Safety

The Feature Store does not generate entries, stops, targets, confidence, expected
value, win rates or recommendations. It exists solely to make future historical
outcome and similarity calculations reproducible and evidence-backed. There is no
broker, live-order, paper-order, alert, LLM or frontend write path.
