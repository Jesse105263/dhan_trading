# Project Status

## Current Status

Version 3 is the active approved implementation contract. V3.0 — Research
Contract and Benchmark Baseline is committed at `a3ed736`. V3.0.5 — Data Provider
& Licensing Strategy is committed at `e1c3618`. V3.1 — Historical Data Foundation
is committed at `fc20734`. V3.2 — Continuous Market Collection is committed at
`885883c`. V3.3 — Outcome Engine V2 is implemented pending repository-owner
review. Migration `025` adds immutable policy, run, canonical multi-horizon
outcome and exact path lineage. Only deterministic local fixtures were used; no
live provider, recommendation or downstream intelligence change exists.

Version 2 is complete. V2.0.1 — Architecture & Product Decisions,
V2.0.2 — Frontend Project Foundation, V2.0.3 — Design System and V2.0.4 —
Application Shell, V2.0.5 — Market Overview & Opportunity Scanner and V2.0.6 —
Symbol Intelligence Workspace, V2.0.7 — Market Memory Foundation and V2.0.8 —
Feature Store, V2.0.9 — Historical Outcome Engine, V2.1.0 — Similarity Engine and
V2.1.1 — Trade Opportunity Engine, V2.1.2 — News & Event Intelligence and V2.1.3
— AI Trading Analyst are complete. The final milestone, V2.1.4 — Intelligence
Release Hardening & Handoff, was committed at `ba6c0a2`. The Version 2 core
intelligence roadmap is complete and preserved.

See `docs/V2_PRODUCT_DEFINITION.md`, `docs/V2_ARCHITECTURE.md` and
`docs/V2_ROADMAP.md`.

See `docs/V3_ROADMAP.md`, `docs/V3_RESEARCH_CONTRACT.md`,
`docs/V3_DATA_PROVIDER_STRATEGY.md`, `docs/HISTORICAL_DATA_FOUNDATION.md`,
`docs/CONTINUOUS_MARKET_COLLECTION.md` and
`docs/V3_RELEASE_READINESS_CHECKLIST.md` for the active work.

## Version 1 Release Status

Version 1.0 is complete and approved.

Milestone 4.6 — Version 1.0 Release Hardening is complete. All automated,
PostgreSQL, migration, backup/restore, runtime and release-readiness verification
passed. No migration `018` was required.

Version 1 remains the stable historical baseline. Version 2 uses separate
`V2.0.x` numbering and preserves all Version 1 safety boundaries.

## Repository Checkpoint

The Version 1 documentation-closure checkpoint is
`555a373 close Version 1.0 documentation`.
The release-hardening implementation checkpoint is
`030ade7 add release readiness verification`.

## Completed Milestones

### Phase 1 — Stable Market Core

- Infrastructure and local containers
- PostgreSQL and Redis
- Ordered database migrations with checksums
- Repository contracts
- Failure persistence and sanitization
- Operational metrics and health reporting
- Production equity collection, snapshots and features
- Scheduler, market calendar and PostgreSQL locks

### Phase 2 — Option Data Platform

- 2.1 Derivative Contract Schema
- 2.2 Derivative Security Master Import
- 2.3 Expiry Repository and Service
- 2.4 Option-Chain Collector
- 2.5 Option Analytics
- 2.6 Option Analytics Pipeline Integration
- 2.7 Option Analytics History and Change Detection

### Phase 3 — Decision and Evaluation Platform

- 3.1 Ranking Engine
- 3.2 Contract Selection
- 3.3 Risk Engine
- 3.4 Signal Engine
- 3.5 Market Replay
- 3.6 Backtesting Engine

### Phase 4 — Product Surface

- 4.1 Read-Only API
- 4.2 Private Read-Only Dashboard
- 4.3 Alerts
- 4.4 AI Copilot
- 4.5 Paper Trading

### Release Hardening

- Read-only release-readiness models, repository, service and CLI
- Deterministic PASS, FAIL and SKIP results
- Migration `001`–`017` inventory and checksum audit
- Persisted lineage, operational-state and execution-schema audits
- Operational runbook and release-readiness checklist
- Focused unit and isolated PostgreSQL integration coverage
- Minimal Copilot execution-refusal fix for verified live-order wording

## Production Data Verification

- Dhan security-master rows processed: 215,940
- Eligible derivative contracts imported: 68,406
- Rejected import rows: 0
- Import is idempotent
- Real RELIANCE option chains collected and persisted
- Real option analytics, history comparison, ranking, contract selection, risk assessment, signals, replay and backtest verified

## Database Migrations

- `001_initial_platform_schema.sql`
- `002_pipeline_failures.sql`
- `003_stage_metrics.sql`
- `004_scheduler_foundation.sql`
- `005_derivative_contracts.sql`
- `006_derivative_security_master_imports.sql`
- `007_option_chain_collections.sql`
- `008_option_chain_analytics.sql`
- `009_option_analytics_changes.sql`
- `010_option_rankings.sql`
- `011_option_contract_selections.sql`
- `012_option_risk_assessments.sql`
- `013_option_signals.sql`
- `014_market_replay.sql`
- `015_option_backtesting.sql`
- `016_alerts.sql`
- `017_paper_trading.sql`
- `018_feature_store.sql`
- `019_historical_outcomes.sql`
- `020_similarity_engine.sql`
- `021_trade_opportunity_engine.sql`
- `022_news_event_intelligence.sql`
- `023_historical_data_foundation.sql`
- `024_continuous_market_collection.sql`
- `025_outcome_engine_v2.sql`

Migrations `018`–`022` remain the immutable Version 2 Feature, Outcome,
Similarity, Opportunity and Event stores. Migrations `023`–`025` add the isolated
Version 3 historical, collection and Outcome V2 stores without changing them.

Milestones 4.1 and 4.2 required no migrations because they are read-only surfaces over existing tables. Milestone 4.3 adds auditable alerts in migration 016, and Milestone 4.5 adds isolated paper state in migration 017.

## Latest Verification

V3.3 verification: compileall passed; standard and PostgreSQL-enabled suites each
ran 278 tests, with 43 expected database-gated skips in the standard suite and
five documented skips in the PostgreSQL suite. Migration `025` applied once and
an idempotent rerun applied zero. The fixed-cutoff operator rerun returned the
same empty-population run ID. Readiness returned 13 PASS, 0 FAIL and six optional
empty-data SKIPs.

V3.2 verification: compileall passed; standard and PostgreSQL-enabled suites each
ran 270 tests, with 41 expected database-gated skips in the standard suite and
five documented skips in the PostgreSQL suite. Migration `024` applied once and
an idempotent rerun applied zero. All fixture commands passed. Release readiness
returned 13 PASS, 0 FAIL and five optional empty-data SKIPs.

V3.1 verification: compileall passed; standard and PostgreSQL-enabled suites each
ran 259 tests, with 39 expected database-gated skips in the standard suite and
five documented skips in the PostgreSQL suite. Migration `023` applied once and
an idempotent rerun applied zero. Release readiness found all 23 migrations and
returned 11 PASS, 0 FAIL and six optional empty-data SKIPs, including the empty
historical foundation.

V2.1.4 verification: compileall passed; standard and PostgreSQL suites each ran
240 tests; frontend lint, 39 tests, build and formatting passed. Expanded
readiness returned 14 PASS, 0 FAIL and 2 acceptable empty-data SKIPs. See
`docs/V2_RELEASE_READINESS_CHECKLIST.md`.

Milestone 4.6 implementation verification completed successfully:

- Compileall: passed
- Standard suite: 176 tests run, 26 expected opt-in database skips
- Full PostgreSQL-enabled suite on `dhan_release_test_46`: 176 tests run
- Result: OK
- Expected skips: 2 production-data-dependent tests when no persisted signal run was available
- Production/restored readiness: 8 PASS, 0 FAIL, 2 valid empty-data SKIPs
- Fresh database: 17 migrations applied; idempotent re-run applied 0
- Backup restore completed only into `dhan_release_test_46`
- Read API/dashboard runtime smoke: healthy; write request rejected with HTTP 405
- Copilot live-order wording defect found, minimally fixed and regression-tested
- Production records were not modified or deleted
- `git diff --check`: clean

## Read-Only API

Start locally:

```bash
python -m scripts.run_read_api
```

Default address:

```text
http://127.0.0.1:8080
```

Resources:

- `rankings`
- `selections`
- `risk`
- `signals`
- `replays`
- `backtests`

See `docs/API.md` for the full contract.

## Safety Boundaries

- LLMs do not execute trades.
- The read API is GET-only.
- The API does not invoke Dhan.
- The API does not trigger calculations.
- The API does not modify persisted records.
- Market replay and backtesting use persisted data only.
- Existing production equity and option pipelines remain separate and backward compatible.

## Private Dashboard

Start the read API with `python -m scripts.run_read_api`, start the dashboard with `python -m scripts.run_dashboard`, and open `http://127.0.0.1:8081`. See `docs/DASHBOARD.md`.

## Alerts

Run `python -m scripts.generate_alerts` for the default private console channel. Source selection and private-webhook configuration are documented in `docs/ALERTS.md`.

## AI Copilot

Run `python -m scripts.ask_copilot "Explain the latest ranking" --symbol RELIANCE` while the read API is available. See `docs/COPILOT.md`.

## Paper Trading

Use `python -m scripts.paper_trade` to open, mark, close and inspect isolated simulated positions. See `docs/PAPER_TRADING.md`.

## Next Activity

Review and commit V3.3. The approved next milestone remains V3.4 — Feature Store
V2. Provider acquisition remains blocked by the documented licensing gates.

Existing Version 1.0 safety boundaries remain unchanged. See `docs/NEXT_TASK.md`,
`docs/OPERATIONS_RUNBOOK.md` and `docs/RELEASE_READINESS_CHECKLIST.md`.
