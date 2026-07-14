# Trade Opportunity Engine

## Objective and Boundary

V2.1.1 turns persisted historical analogues into deterministic, auditable
opportunity assessments. It consumes only Feature Store vectors, persisted
Similarity Engine runs/matches, and persisted Historical Outcomes. It does not
call collectors, Dhan, brokers, alerts, paper trading, AI, or LLMs.

The first model, `historical-long-opportunity-v1`, supports long underlying
reference levels only. Historical Outcome Engine paths describe underlying spot,
not option-premium paths. Entry, stop and target values must therefore never be
presented as option prices.

## Evidence Eligibility

Recommendation fields require all of the following:

- a persisted query-vector `spot_price`;
- at least five similarity matches with `EXPIRY_COMPLETE` outcomes;
- non-null objective closing return, MFE, MAE and win/loss classification;
- positive average closing return;
- historical win rate of at least 50%;
- valid ordered long zones and positive risk/reward.

Fewer than five classified outcomes returns `INSUFFICIENT_EVIDENCE`. Adequate but
non-positive evidence returns `NO_OPPORTUNITY`. Both states keep entry, stop,
targets, score and risk/reward null. This policy never fabricates confidence.

## Deterministic Calculations

For eligible long evidence, using the current persisted spot:

- entry-zone high: current spot;
- entry-zone low: spot adjusted by the 25th percentile historical MAE;
- stop: spot adjusted by the 10th percentile historical MAE;
- target 1: spot adjusted by median historical MFE;
- target 2: spot adjusted by the 75th percentile historical MFE;
- expected value: mean classified closing return;
- win rate: persisted wins divided by classified outcomes;
- risk/reward: target-1 reward from entry midpoint divided by stop risk.

Quantiles use deterministic nearest-rank selection. The opportunity score ranks
eligible records only: 40% mean similarity, 30% win rate, 20% capped positive
expected return, and 10% evidence quality. It is a ranking score, not confidence.

Evidence quality combines classified sample size, average similarity and shared
feature coverage. It describes evidence completeness, not probability of profit.

## Persistence and Lineage

Migration `021_trade_opportunity_engine.sql` adds:

- `trade_opportunity_runs` for versioned batch identity and source run IDs;
- `trade_opportunities` for states, ranking, levels, statistics and reasons;
- `trade_opportunity_evidence` for exact similarity-match, vector and outcome
  lineage.

UUIDv5 identities and unique constraints make materialization idempotent. Source
Market Memory, Feature Store, Outcome Store and Similarity records are immutable.

## Operator Command

```bash
python -m scripts.materialize_trade_opportunities
python -m scripts.materialize_trade_opportunities --similarity-run-id <UUID>
```

The optional `--limit` is bounded to 1–500. Materialization writes only the
approved Opportunity Store.

## Read API

- `GET /api/v2/trade-opportunities`
- `GET /api/v2/trade-opportunities/{opportunity_id}`

The list supports `symbol`, `state`, and limit 1–200. Ordering is deterministic:
eligible first, then no-opportunity and insufficient-evidence records, with score,
observation time and UUID tie-breaking. Detail returns exact evidence lineage.
Existing ranking endpoints under `/api/v2/opportunities` and all `/api/v1`
contracts remain unchanged.

## Frontend

`/trade-opportunities` provides the ranked, filterable workspace.
`/trade-opportunities/{id}` displays levels, statistics, evidence quality,
reasons for/against, limitations and exact vector/outcome lineage. Missing values
remain visibly unavailable. No browser-side financial calculation occurs.

## Limitations

- This model cannot propose option-premium entries, stops or targets.
- Sparse classified history produces no recommendation fields.
- Similar historical behavior does not guarantee future results.
- News and event context is deferred to V2.1.2.

V2.1.2 attaches event context after calculation without changing any opportunity
level, statistic, score, rank or eligibility. See `docs/NEWS_EVENT_INTELLIGENCE.md`.
