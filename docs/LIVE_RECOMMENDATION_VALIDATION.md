# Live Recommendation Validation

Version 3.8 is an offline, shadow-only observation layer. It permanently freezes
each V3.7 evaluation and its exact option contract, predicted metrics, reasons,
versions and point-in-time lineage. Database constraints keep
`operationally_trusted=false`; no order, broker, alert or paper-to-live path exists.

## Snapshot and observation lifecycle

Deterministic snapshots preserve eligible, rejected and abstained evaluations.
Canonical accepted option bars available by an explicit cutoff append immutable
observations. An entry-zone touch creates a conservative simulated fill, unless an
explicit user-journal fill already exists. User fills are observations only and
never cause execution. Unfilled, expired, unresolved and insufficient paths remain
first-class results with unsupported fields null.

After fill, ordered bars determine target or stop first touch. A bar touching both
is `INSUFFICIENT_PATH`, never guessed. Complete paths calculate MFE, MAE, time
under water, target/stop timing, gross return and net return after versioned costs.
Timeout and expiry are explicit. Every observation retains bar-revision and raw-
manifest lineage; later data creates a later outcome rather than rewriting one.

## Failure classification

Classifications are immutable and limited to deterministic evidence:
`MARKET_FAILURE`, `MODEL_FAILURE`, `CALIBRATION_FAILURE`, `LIQUIDITY_FAILURE`,
`FILL_FAILURE`, `EVENT_SHOCK`, `DATA_FAILURE`, `POLICY_REJECTION`, `UNCLASSIFIED`
and `INSUFFICIENT_EVIDENCE`. Event shock is never inferred without explicit event
evidence. Unsupported causality remains `UNCLASSIFIED`.

## Metrics, drift and suspension

Versioned rolling reports preserve total/eligible/rejected counts, abstention,
fill and unresolved rates. Once the configured minimum population exists they add
win rate, realized and predicted net EV, EV error, Brier score, calibration error,
interval coverage, MFE/MAE, slippage, fill quality and target/stop/timeout rates.
Reports segment by strategy, instrument, regime, horizon, liquidity, evidence
quality and recommendation-policy version. Unsupported statistics remain null.

Drift policies compare calibration, win rate, EV, feature, population, fill,
liquidity and data-quality measures using `HEALTHY`, `WATCH`, `DEGRADED`,
`SUSPENDED` and `INSUFFICIENT_EVIDENCE`. Fewer than 60 distinct shadow sessions
cannot establish operational trust. A threshold breach appends a suspension; it
never changes old snapshots, models or thresholds.

## Persistence and commands

Migration `030` adds immutable validation policies, snapshots, observations,
fills, outcomes, failure evidence, metric runs/segments, drift evaluations and
suspensions. UUIDv5 identities and natural uniqueness make reruns idempotent.

```bash
python -m scripts.materialize_recommendation_validation --recommendation-id UUID
python -m scripts.materialize_recommendation_validation --fixture
python -m scripts.compute_validation_metrics --fixture
python -m scripts.evaluate_recommendation_drift --fixture
```

For the first command, an existing snapshot UUID is reused; otherwise the UUID is
resolved as a V3.7 evaluation and snapshotted before observation.

Fixtures are deterministic local shadow evidence and always print `trusted=false`.
No live provider is activated. The 60-session live-shadow requirement, licensed
coverage, population metrics and operational recommendation trust remain unmet.
V3.9 is the next milestone and owns any future explicit offline promotion process.
V3.9 uses mature shadow evidence only for offline research. Registry promotion
never alters snapshots or creates operational trust.
