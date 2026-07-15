# Version 3 Roadmap — AI Trading Intelligence

## Implementation contract

Version 3 builds a private institutional-grade AI Trading Intelligence Platform
that eventually produces statistically justified, calibrated recommendations
with an exact instrument and option contract, entry zone, stop, targets,
historical win rate, expected value after costs, Prediction Interval / Confidence
Interval (where statistically appropriate), evidence quality, similar-setup
count, reasons for and against, eligibility and complete point-in-time lineage.

Version 3 preserves Version 2 behavior and APIs. It adds no live trade execution.
All milestones require deterministic processing, immutable lineage,
reproducibility, leakage prevention, statistical rigor and abstention when
evidence is weak.

## Ordered milestones

### V3.0 — Research Contract and Benchmark Baseline

Define decision, outcome, cost, sample, split, calibration, uncertainty and
eligibility semantics. Fix purged walk-forward train, validation, calibration and
test periods; register naive and Version 2 baselines; report coverage, abstention,
win rate, expected value, Prediction Interval / Confidence Interval (where
statistically appropriate) coverage when supported, calibration, risk and costs.
Every result must be reproducible and future models must outperform registered
baselines with statistically supported evidence. Estimated effort: 1–2 weeks.

### V3.0.5 — Data Provider & Licensing Strategy

Compare viable providers on depth, intraday and chain history, Greeks, IV,
corporate actions, news, events, quotas, reliability, licensing and price.
Approve a primary and backup provider, provider-neutral downstream contract,
storage forecast and acquisition/collection budget. The strategy selects DhanHQ
historical, TrueData continuous and DhanHQ backup, all subject to written licence
confirmation, and defines V3.1 procurement gates in
`docs/V3_DATA_PROVIDER_STRATEGY.md`. No integration or paid activation is part of
this milestone. Estimated effort: about one week.

### V3.1 — Historical Data Foundation

Acquire at least five years of daily and at least two years of sustainable
intraday history for the supported F&O universe, including underlying, futures,
options, chains where licensed, volatility, reference metadata, corporate actions
and point-in-time events. Require immutable checksummed raw sources, restartable
idempotent imports, survivorship-safe identities, coverage reporting and revision
leakage tests. Targets are 95% expected underlying-session coverage and 90%
supported derivative coverage. Estimated effort: 4–7 weeks excluding procurement.

Foundation checkpoint: migration `023`, provider-neutral contracts, immutable raw
payload/manifests, temporal instrument mappings, canonical instrument/bar/action
revisions, retention metadata, checksums, deduplication and conflict quarantine
are implemented in `docs/HISTORICAL_DATA_FOUNDATION.md`. Provider acquisition and
the coverage targets remain blocked and unmet because this checkpoint performs no
authentication, download or backfill.

### V3.2 — Continuous Market Collection

Continuously collect the same canonical contracts with session policy, gap repair,
late-data reconciliation, quotas, freshness and anomaly monitoring. Require 20
unattended market sessions, 99% completion or bounded repair, deduplication, exact
source/revision lineage and continuous coverage reporting. Estimated effort: 3–5
weeks.

Framework checkpoint: migration `024`, deterministic session policy, provider-
neutral work, immutable attempts, restart recovery, quotas, gaps, bounded repairs,
reconciliation lineage, health and fixture-only operator commands are implemented.
The 20-session/99% live targets remain unevaluated because no licensed live
provider or schedule is activated. V3.3 remains the next milestone.

### V3.3 — Outcome Engine V2

Create underlying and actual selected-contract labels across intraday, session,
multi-session and expiry horizons. Persist fills, triple-barrier first touch,
targets, stops, timeout, expiry, MFE, MAE, duration, liquidity and net returns
after costs. Preserve censored, ambiguous, unfilled and missing states; require
deterministic path reconstruction, at least 80% supported-population completeness
or explained exclusions, and structural future-data isolation. Estimated effort:
3–5 weeks.

Framework checkpoint: migration `025` implements versioned duration, session and
expiry labels for canonical underlying and option bars, exact path/manifests,
costs, optional target/stop outcomes, MFE, MAE, drawdown, realized volatility,
volatility-adjusted return, aggregate expectancy/payoff ratio and explicit
unknown/insufficient/ambiguous states. Corporate actions fail closed unless the
path is already adjusted. Population completeness remains unevaluated because no
licensed historical population exists. V3.4 remains next.

### V3.4 — Feature Store V2

Build versioned point-in-time price, volatility, volume, liquidity, option-chain,
futures, regime, cross-sectional, expiry and event features with exact formulas,
availability timestamps and source lineage. Training and live materialization must
share definitions; leakage, drift, missingness and distribution checks are
mandatory, with 90% declared coverage for core features. Estimated effort: 4–6
weeks.

Framework checkpoint: migration `026` implements immutable feature schemas,
definitions, materialization runs, vectors and values over point-in-time canonical
bar revisions. The first schema covers price, returns, volatility, volume,
derivatives, liquidity, temporal and regime families, preserves missing values,
records normalization metadata and exact revision lineage, and remains compatible
with V2 consumers through isolation. Population coverage, drift/distribution
baselines and additional option-chain, event and cross-sectional families remain
unevaluated until licensed canonical evidence exists. V3.5 remains next.

### V3.5 — Similarity Engine V2

Build train-window-normalized, regime-aware, strategy-aware analogues with feature
group weights, temporal diversity, duplicate suppression and out-of-distribution
abstention. Evaluate learned and transparent distances against Version 2 using
outcome consistency, precision at K, expected-value uplift, stability, effective
sample size and coverage. Require exact scaler/model/candidate lineage and p95
retrieval below one second for one million vectors. Estimated effort: 3–5 weeks.

### V3.6 — Opportunity Engine V2

Produce provisional strategy-aware candidates with exact option contract, entry,
stop, targets, horizon, historical win rate, net expected value, sample evidence,
quality inputs and deterministic reasons. Use actual option-premium evidence,
liquidity and fill feasibility. Prevent episode concentration and abstain for weak,
contradictory, illiquid or out-of-distribution evidence. Candidates remain
non-recommendational until V3.7. Estimated effort: 4–6 weeks.

### V3.7 — Calibration, Uncertainty, and Recommendation Policy

Calibrate probabilities by justified strategy/regime populations and calculate
Prediction Interval / Confidence Interval (where statistically appropriate),
effective sample size and sensitivity. Eligibility requires acceptable
calibration and interval coverage, positive conservative after-cost value,
liquidity, diversity, distribution and data-quality gates. Similarity and ranking
alone never authorize recommendations; degradation suspends policy. Estimated
effort: 2–4 weeks.

### V3.8 — Live Recommendation Validation

Immutably freeze each recommendation and observe fill, target/stop ordering,
expiry, MFE, MAE, return, duration, failure cause, contribution and drift without
execution. Track rolling acceptance, coverage, win rate, value, calibration,
interval coverage, slippage and population/feature drift, including rejected,
abstained and unfilled cases. Mature outcomes may enter later versioned research,
but models never self-modify silently. Require at least 60 shadow market sessions.
Estimated effort: 3–5 weeks plus evidence time.

### V3.9 — Institutional Research, Validation, and Model Governance

Register immutable datasets, features, labels and models; run declarative
walk-forward champion/challenger research; audit leakage, survivorship, selection,
overlap and multiple testing. Promotion requires frozen out-of-sample evidence,
data, leakage and calibration audits, live shadow results and owner approval;
rollback never rewrites history. Estimated effort: 3–5 weeks incrementally.

### V3.10 — Scale and Operational Hardening

Partition and incrementally process proven workloads, checkpoint backfills, use
bounded deterministic parallelism and bulk operations, enforce performance
regressions and fail closed. Require one-million-observation service objectives,
documented retention/capacity/recovery, clean-environment restoration and a
20-session soak without gaps, duplicates, silent failures or lineage violations.
Estimated effort: 3–5 weeks.

## Ordering rationale

The contract defines truth first; provider selection prevents licensing and schema
lock-in; historical and continuous data remove the evidence bottleneck; outcomes
establish ground truth before features and similarity; opportunity construction
is separated from calibration authorization; live validation measures real drift;
governance controls promotion; and scale is applied only to proven workloads.

Estimated critical path: approximately 31–51 person-weeks plus statistically
meaningful live-validation time.
