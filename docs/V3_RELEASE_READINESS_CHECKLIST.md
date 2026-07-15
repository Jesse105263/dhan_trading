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
- [x] Repository-owner review and commit are complete (`a3ed736`).

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

## V3.0.5 — Data Provider & Licensing Strategy

- [x] Official documentation was reviewed for the required India-focused,
  exchange, enterprise and relevant international providers.
- [x] The comparison records depth, derivatives, OI, IV/Greeks, depth, delivery,
  quotas, reliability, licensing, price, gaps and role suitability.
- [x] Unpublished commercial rights are explicitly `UNKNOWN — PROVIDER
  CONFIRMATION REQUIRED`.
- [x] DhanHQ is selected as primary historical and live backup; TrueData is
  selected as primary continuous/live, subject to written licensing confirmation.
- [x] NSE/BSE, RBI/MoSPI and a bounded news strategy are identified as specialist
  sources.
- [x] Provider-neutral interfaces, identifiers, mappings, failover, conflicts,
  checksums, manifests, licensing and retention metadata are defined.
- [x] Low, expected and high storage estimates and planning-only cost envelopes
  are documented.
- [x] V3.1 entry requirements block ingestion until licensing, budget, coverage,
  storage and canonical-contract evidence are approved.
- [x] No provider integration, migration, dependency, collector or credential was
  added; no provider was contacted, purchased, configured or called.
- [x] Standard Python verification and Git whitespace checks pass.
- [ ] Repository-owner review and commit are complete.
