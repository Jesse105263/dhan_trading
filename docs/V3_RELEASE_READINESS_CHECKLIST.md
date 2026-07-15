# Version 3 Release Readiness Checklist

## V3.0 — Research Contract and Benchmark Baseline

- [x] Version 3 roadmap is recorded as the implementation contract.
- [x] Fixed train, validation, calibration and untouched test periods are versioned.
- [x] Purge, embargo and minimum evidence thresholds are explicit.
- [x] Naive controls and Version 2 ranking/opportunity baselines are registered.
- [x] The report consumes persisted point-in-time Version 2 facts only.
- [x] Sparse populations return null metrics and `INSUFFICIENT` evidence.
- [x] The contract has a deterministic SHA-256 checksum.
- [x] The command is SELECT-only and invokes no provider, model or execution path.
- [x] Unit and isolated PostgreSQL integration coverage is present.
- [x] Required verification is recorded for the implementation checkpoint.
- [ ] Repository-owner review and commit are complete.

V3.0 does not establish statistically reliable recommendations. Version 2 has no
expiry-classified population sufficient for that claim, and its outcomes remain
underlying reference outcomes rather than option-premium returns after costs.

## Verification evidence

- `python -m compileall app services scripts tests`: passed.
- `python -m unittest discover -s tests -v`: 248 passed, 37 PostgreSQL-gated skips.
- `RUN_DB_INTEGRATION_TESTS=1 python -m unittest discover -s tests -v`: 248
  passed, five documented data/isolated-database skips.
- `python -m scripts.benchmark_recommendations`: passed; nine test-period vectors,
  zero classified outcomes and explicit `INSUFFICIENT` baselines.
- `python -m scripts.verify_release`: release ready with 11 PASS, 0 FAIL and five
  documented empty optional-data SKIPs.
