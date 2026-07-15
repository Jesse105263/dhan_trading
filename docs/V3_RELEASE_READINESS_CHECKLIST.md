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
- [x] Repository-owner review and commit are complete (`fc20734`).

V3.1 verification evidence:

- `python -m compileall app services scripts tests`: passed.
- `python -m unittest discover -s tests -v`: 259 passed, 39 expected
  PostgreSQL-gated skips.
- `RUN_DB_INTEGRATION_TESTS=1 python -m unittest discover -s tests -v`: 259
  passed, five documented data/isolated-database skips.
- Migration `023` applied once; idempotent rerun applied zero migrations.
- `python -m scripts.verify_release`: 11 PASS, 0 FAIL and six documented
  optional empty-data SKIPs, including the empty historical foundation.

## V3.2 — Continuous Market Collection

- [x] Deterministic pre-open, regular, close, post-close, holiday and expiry policy exists.
- [x] Every supported dataset has a provider-neutral deterministic work contract.
- [x] Migration `024` persists schedules, work, immutable attempts, gaps, repairs,
  quota state, quality incidents and reconciliation results.
- [x] Claims are bounded, restartable and overlap-safe; retries are bounded.
- [x] Partial scope, unavailable providers and quota exhaustion are explicit.
- [x] Successful fixture bytes use V3.1 raw/canonical checksum and revision policy.
- [x] Gap and repair IDs are deterministic and idempotent.
- [x] Late revisions and cross-source conflicts retain V3.1 lineage/quarantine.
- [x] Fixture-only commands and read-only status exist; `/api/v1` is unchanged.
- [x] No live adapter, credential, external call or production schedule was added.
- [ ] Twenty live sessions and 99% completion are not evaluated while activation is blocked.
- [x] Repository-owner review and commit are complete (`885883c`).

V3.2 verification evidence:

- Compileall passed.
- Standard suite: 270 tests, 41 expected PostgreSQL-gated skips.
- PostgreSQL suite: 270 tests, five documented data/isolated-database skips.
- Migration `024` applied once; rerun applied zero; all 24 checksums match.
- All fixture commands passed; reconciliation and work scheduling reruns were idempotent.
- Readiness: 13 PASS, 0 FAIL and five optional empty-data SKIPs.

## V3.3 — Outcome Engine V2

- [x] Duration, session-count and expiry horizons are immutable policy inputs.
- [x] Accepted canonical underlying and option bars are supported without proxies.
- [x] Anchor/path revisions are selected only when available by the run cutoff.
- [x] Gross/net return, MFE, MAE, drawdown, realized volatility and adjusted return are deterministic.
- [x] Aggregate expectancy and payoff ratio use complete net-return evidence only.
- [x] Missing horizons and expiries are `UNKNOWN`; sparse paths and corporate actions fail closed.
- [x] Same-bar target/stop ambiguity never guesses first-touch order.
- [x] Migration `025` persists immutable policy, run, outcome and exact path lineage.
- [x] UUIDv5 and database constraints make fixed-cutoff reruns idempotent.
- [x] V2 outcomes, Similarity, Opportunity, Analyst, recommendations and `/api/v1` are unchanged.
- [ ] Eighty-percent supported-population completeness is unevaluated without licensed history.
- [ ] Repository-owner review and commit are complete.

V3.3 verification evidence:

- Compileall passed.
- Standard suite: 278 tests, 43 expected PostgreSQL-gated skips.
- PostgreSQL suite: 278 tests, five documented data/isolated-database skips.
- Migration `025` applied once; rerun applied zero; all 25 checksums match.
- Fixed-cutoff command rerun returned the same run ID and explicit empty population.
- Readiness: 13 PASS, 0 FAIL and six optional empty-data SKIPs.

## V3.4 — Feature Store V2

- [x] Definitions are versioned with exact formulas, families and minimum history.
- [x] Missing-value and normalization policies are metadata, never fabricated values.
- [x] Canonical bar and instrument revisions are selected point in time.
- [x] Deterministic runs, vectors and definitions make fixed-cutoff reruns idempotent.
- [x] Values retain exact source revision IDs and checksums; vectors retain quality metrics.
- [x] Migration `026` persists immutable schemas, definitions, runs, vectors and values.
- [x] Release readiness audits counts, schema/run/anchor lineage and future leakage.
- [x] V2 Feature Store and all current consumers remain backward compatible.
- [ ] Core-population coverage, drift and distributions remain unevaluated without licensed history.
- [ ] Repository-owner review and commit are complete.

V3.4 verification evidence:

- Compileall passed.
- Standard suite: 284 tests, 45 expected PostgreSQL-gated skips.
- PostgreSQL suite: 284 tests, five documented data/isolated-database skips.
- Migration `026` applied once; rerun applied zero; all 26 checksums match.
- Fixed-cutoff command rerun returned the same run ID and explicit empty population.
- Readiness: 13 PASS, 0 FAIL and seven optional empty-data SKIPs.

## V3.5 — Similarity Engine V2

- [x] Multiple transparent distance models and ranking strategies are versioned.
- [x] Feature and family weights plus dynamic selection are immutable policy.
- [x] Regime, liquidity, volatility, age, subject and interval controls are explicit.
- [x] Candidate observations and availability are strictly before/by cutoff.
- [x] Outcomes are attached after ranking and must complete before the query.
- [x] Diagnostics, quality, exact feature/candidate/outcome lineage and checksums persist.
- [x] Fixed-policy reruns are deterministic and idempotent.
- [x] Weak populations are `INSUFFICIENT_EVIDENCE`.
- [x] V2 Similarity and downstream consumers remain unchanged.
- [ ] Population quality and million-vector performance remain unevaluated.
- [ ] Repository-owner review and commit are complete.

V3.5 verification evidence:

- Compileall passed.
- Standard suite: 289 tests, 46 expected PostgreSQL-gated skips.
- PostgreSQL suite: 289 tests, five documented data/isolated-database skips.
- Migration `027` applied once; rerun applied zero; all 27 checksums match.
- Deterministic fixture materialization reran with the same run and match IDs.
- Readiness: 13 PASS, 0 FAIL and eight optional empty-data SKIPs.

## V3.6 — Opportunity Engine V2

- [x] Exact option contract and actual premium paths are required for levels.
- [x] Strategy, horizon, training boundary, costs, fills and quantiles are versioned.
- [x] Win rate, net expected value and effective sample size use complete evidence.
- [x] Symbol/contract, expiry, regime and episode concentration can force abstention.
- [x] Liquidity, fill, moneyness, expiry and distribution gates fail closed.
- [x] Unsupported fields remain null for every abstention state.
- [x] Feature, contract, similarity, outcome and match lineage is immutable.
- [x] V2 Opportunity and Analyst behavior remains unchanged.
- [ ] Population recommendation quality remains unevaluated without licensed history.
- [ ] Repository-owner review and commit are complete.

V3.6 verification evidence:

- Compileall passed.
- Standard suite: 294 tests, 48 expected PostgreSQL-gated skips.
- PostgreSQL suite: 294 tests, five documented data/isolated-database skips.
- Migration `028` applied once; rerun applied zero; all 28 checksums match.
- Deterministic fixture-backed service/operator path reran idempotently.
- Readiness: 13 PASS, 0 FAIL and nine optional empty-data SKIPs.

## V3.7 — Calibration, Uncertainty, and Recommendation Policy

- [x] Fixed partitions, purge, embargo and terminal cutoffs prevent leakage.
- [x] Transparent calibration, uncertainty, abstentions and lineage are immutable.
- [x] Fixture evidence remains insufficient, uncalibrated and never trusted.
- [x] V2 behavior, `/api/v1`, providers and execution remain unchanged.
- [ ] Licensed population quality and live trust are unevaluated.
- [ ] Repository-owner review and commit are complete.

V3.7 verification evidence: compileall passed; standard and PostgreSQL suites each
ran 306 tests with 50 and five expected skips respectively; migration `029`
applied once and reran with zero changes; 29 checksums match; readiness reports
13 PASS, zero FAIL and ten optional SKIPs; both fixtures failed closed.

## V3.8 — Live Recommendation Validation

- [x] Recommendation snapshots preserve exact contracts, predictions, versions and lineage.
- [x] Eligible, rejected, abstained, unfilled and incomplete states remain visible.
- [x] Canonical paths support deterministic fills, first touch, MFE/MAE and net return.
- [x] Rolling metrics enforce minimum samples and unsupported values remain null.
- [x] Drift and suspension policies are versioned and immutable.
- [x] Operational trust is constrained false; no execution or self-learning path exists.
- [ ] Sixty live shadow sessions and population quality remain unevaluated.
- [ ] Repository-owner review and commit are complete.

V3.8 verification evidence: compileall passed; standard and PostgreSQL suites ran
319 tests with 52 and five expected skips respectively; migration `030` applied
once and reran with zero changes; all 30 checksums match; readiness reports
13 PASS, zero FAIL and eleven optional SKIPs; fixture reruns were deterministic.
