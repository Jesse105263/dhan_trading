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
- [x] Repository-owner review and commit are complete (`e1c3618`).

## V3.1 — Historical Data Foundation

- [x] Provider-neutral source, retention, raw-envelope and adapter interfaces exist.
- [x] Exact raw bytes and immutable manifests retain source, entitlement, request,
  coverage, parent, schema, adapter, count and checksum lineage.
- [x] Canonical instruments are independent of provider IDs and preserve
  underlying, futures and option-contract terms through revisions.
- [x] Provider symbol/security-ID mappings are temporal and reject overlaps.
- [x] Historical bars preserve OHLCV, OI, optional quote/trade values, adjustment
  state, availability and revision lineage without imputation.
- [x] Corporate actions preserve original/normalized terms and revisions.
- [x] Exact replay deduplicates; same-source changes append revisions; conflicting
  cross-source bars are quarantined with quality incidents.
- [x] Unknown or denied raw/normalized retention fails before adapter invocation.
- [x] Unit and PostgreSQL integration coverage use deterministic local records only.
- [x] Migration `023` is append-only; migrations `001`–`022` remain unchanged.
- [x] No provider client, credential, historical download, backfill, continuous
  collector, scheduler, API, frontend or execution path was added.
- [ ] Five-year daily, two-year intraday and coverage targets are not evaluated;
  licensed acquisition remains blocked by the provider-strategy gates.
- [ ] Repository-owner review and commit are complete.

V3.1 verification evidence:

- `python -m compileall app services scripts tests`: passed.
- `python -m unittest discover -s tests -v`: 259 passed, 39 expected
  PostgreSQL-gated skips.
- `RUN_DB_INTEGRATION_TESTS=1 python -m unittest discover -s tests -v`: 259
  passed, five documented data/isolated-database skips.
- Migration `023` applied once; idempotent rerun applied zero migrations.
- `python -m scripts.verify_release`: 11 PASS, 0 FAIL and six documented
  optional empty-data SKIPs, including the empty historical foundation.
