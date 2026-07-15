# Calibration, Uncertainty, and Recommendation Policy

Version 3.7 separates provisional Opportunity V2 candidates from recommendation
eligibility. Ranking, similarity, evidence quality and historical win rate are not
confidence and cannot independently authorize eligibility.

Policies freeze strategy, direction, horizon, regimes; train, validation,
calibration and untouched-test boundaries; purge and embargo; and every sample,
uncertainty, quality, drift and conservative-EV threshold. Only complete outcomes
terminal within their partition and cutoff enter lineage. Train/validation are
excluded, calibration fits the mapping, and untouched test is evaluation-only.

The dependency-free service supports empirical equal-width and transparent
monotonic bins. It persists reliability statistics, Brier score, log loss, ECE,
maximum calibration error, test interval coverage where available, net EV and
realized rate. Wilson intervals describe win probability. Deterministic seeded
bootstrap intervals describe returns and EV. Unsupported metrics remain null.

`ELIGIBLE` requires every sample, effective-sample, calibration, uncertainty,
positive conservative EV, concentration, distribution, data-quality, drift,
liquidity, release-readiness and provisional-source gate. Failures return a
specific abstention state. Eligibility is research output, not a trusted
recommendation; V3.8 live validation and owner approval remain mandatory.

Migration `029` adds immutable policies, runs, bins, exact dataset lineage and
evaluations. UUIDv5 identities and checksums make reruns idempotent.

```bash
python -m scripts.materialize_calibration_v2 --policy-id UUID
python -m scripts.evaluate_recommendation_policy --candidate-id UUID --calibration-run-id UUID --policy-id UUID
python -m scripts.materialize_calibration_v2 --fixture
python -m scripts.evaluate_recommendation_policy --fixture
```

The local eight-observation fixture deliberately fails closed and prints
`trusted=false`. Commands call no provider, Dhan, broker or model. Licensed
population calibration, drift performance and recommendation trust are unresolved.
V3.9 retains calibration versions as immutable lineage and cannot refit bins,
change thresholds or reinterpret historical eligibility.
V3.8 snapshots evaluations without changing calibration runs or gates. Eligibility
remains research-only until 60 live shadow sessions and later governance approval.
