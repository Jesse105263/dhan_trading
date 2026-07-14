# Similarity Engine

V2.1.4 audited persisted match lineage and point-in-time ordering with zero
violations. The current eight-match run remains `INSUFFICIENT`.

## Objective

V2.1.0 finds persisted Feature Store observations that most closely resemble a
selected observation. It returns transparent historical analogues and their
persisted Historical Outcome records. It never generates recommendations,
entries, stops, targets, or confidence.

## Model and Features

`option-observation-similarity-v1` uses min-max normalized weighted Manhattan
distance. Ranges use only the query and eligible historical candidates. Distance
is the weighted mean of normalized absolute differences; similarity is
`1 - distance`. Ties sort by observation timestamp then vector UUID.

| Feature | Weight |
| --- | ---: |
| `atm_distance_pct` | 1.0 |
| `total_pcr` | 1.0 |
| `nearby_pcr` | 1.0 |
| `atm_mean_iv` | 1.5 |
| `nearby_mean_iv` | 1.0 |
| `liquidity_coverage` | 1.5 |
| `price_coverage` | 1.0 |
| `spot_price_change` | 1.0 |
| `atm_straddle_change` | 1.0 |
| `total_pcr_change` | 1.0 |
| `atm_mean_iv_change` | 1.0 |
| `time_to_expiry_days` | 1.0 |

Identifiers, timestamps, absolute price/OI fields, ranking policy scores and all
outcomes are excluded. Missing values are skipped, never zero-filled. Candidates
need five shared features. Constant features contribute zero distance. Responses
include overlap counts and feature-level weighted contributions.

## Leakage Prevention

The cutoff defaults to the query timestamp and may only move earlier. The query
vector is excluded; symbol and expiry filters are optional. Outcomes are fetched
only after ranking, so future outcome values cannot influence similarity.

## Persistence and Lineage

Migration `020_similarity_engine.sql` adds `similarity_runs` and
`similarity_matches`. Deterministic UUIDv5 identifiers and unique constraints make
materialization idempotent. Runs preserve configuration, filters, query lineage,
counts and evidence state. Matches preserve rank, diagnostics, vector lineage and
optional Outcome Store lineage. Source Feature and Outcome records are unchanged.

## API and CLI

- `GET /api/v2/similarity/models`
- `GET /api/v2/similarity?vector_id=<uuid>&limit=20`
- `GET /api/v2/similarity/runs/<run_id>`
- `GET /api/v2/similarity/runs/<run_id>/matches`

Analysis accepts `same_symbol`, `same_expiry`, `historical_cutoff`,
`model_version`, and limit 1–100. GET computation never persists. An operator can
persist an auditable run with:

```bash
python -m scripts.materialize_similarity_run --vector-id <UUID> --limit 20
```

Optional flags are `--same-symbol`, `--same-expiry`, and `--historical-cutoff`.
The command never calls Dhan or mutates source market observations.

## Statistics, Evidence and Frontend

Statistics use attached persisted outcomes only: usable/classified counts, win
rate, average/median closing return, average MFE/MAE, and best/worst outcome.
Fewer than three classified outcomes is explicitly `INSUFFICIENT`; unsupported
statistics remain null. Sparse history and zero matches are valid states.

`/memory/similarity` lets the owner choose a symbol and Feature Store vector,
inspect ranked analogues, evidence warnings and exact lineage. It uses the
existing client/design system and performs no financial calculation in-browser.

V2.1.1 may consume persisted similarity runs and Outcome Store evidence. It must
not recompute outcomes or treat similarity alone as a recommendation.
