# Version 3 Research Contract and Benchmark Baseline

## Purpose

V3.0 establishes the statistical research boundary for Version 3 before new data,
features or recommendation models are built. The objective is a private,
institutional-grade AI Trading Intelligence Platform that eventually emits exact
option recommendations only when point-in-time evidence, calibration and
uncertainty policy justify them.

V3.0 does not create recommendations. It benchmarks persisted Version 2 evidence
and reports unsupported metrics as null.

## Versioned contract

`v3-research-contract-v1` fixes:

- decision boundary: predictive inputs must have been available at or before the
  observation timestamp;
- source outcome model: `underlying-through-expiry-v1`;
- purge: 45 calendar days;
- embargo: 7 calendar days;
- minimum evidence threshold: 30 evaluated observations;
- training: 2020-01-01 through 2023-12-31;
- validation: 2024-01-01 through 2024-12-31;
- calibration: 2025-01-01 through 2025-06-30;
- untouched test: 2025-07-01 through 2026-12-31.

The service emits a SHA-256 checksum over the canonical contract manifest. Any
future change requires a new contract version; historical reports retain their
original meaning.

The purge is longer than the currently supported option observation horizon and
the embargo separates adjacent research decisions. V3.0 baselines do not fit
parameters, but all later fitted models must apply both controls within their
walk-forward process.

## Registered baselines

- `always_long`: every persisted vector;
- `deterministic_random_half`: a fixed SHA-256 control sample using the vector ID
  and documented seed;
- `momentum_positive`: persisted positive `spot_price_change`;
- `mean_reversion_negative`: persisted negative `spot_price_change`;
- `v2_ranked`: vectors with persisted Version 2 ranking lineage;
- `v2_opportunity`: persisted Version 2 `ELIGIBLE` opportunity state.

These baselines reuse existing facts. They do not introduce option-premium logic,
infer missing values or modify Version 2 policy.

## Metrics and insufficiency

For each fixed period and baseline the report provides population, selected and
evaluated counts, coverage, abstention rate, precision/win rate, expected and
average realized return, worst/tail return, chronological compounded maximum
drawdown, Brier score and calibration-in-the-large error when a persisted
prediction exists. Unsupported cost-adjusted return, turnover and Prediction
Interval / Confidence Interval (where statistically appropriate) coverage are
present as null. `EXPIRY_COMPLETE` outcomes with non-null return and classification
are the only evaluated observations.

`SUFFICIENT` means only that the baseline has at least 30 evaluated observations.
It is not recommendation eligibility, confidence or statistical validation.
Metrics with no valid observations remain null.

Version 2 outcomes measure underlying spot, not selected option-premium returns.
They do not contain transaction costs, slippage, turnover, capacity, calibrated
probabilities or Prediction Interval / Confidence Interval (where statistically
appropriate). V3.0 therefore does not claim those metrics.

## Operation

Run the SELECT-only JSON report with:

```bash
python -m scripts.benchmark_recommendations
```

The command calls no collector, provider, model, broker, alert or execution path.
It writes no database or filesystem state.

## Promotion boundary

Future research must identify its contract checksum, source-data versions,
feature and outcome versions, model configuration and evaluation periods. No
recommendation may be promoted solely because similarity or a ranking score is
high. Calibration, uncertainty, effective sample size, costs, liquidity,
out-of-distribution checks and abstention policy remain mandatory future gates.
V3.7 fits only on calibration and reserves untouched test for evaluation; its
eligibility result remains non-trusted pending V3.8.
