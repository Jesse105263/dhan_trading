# Project Status

## Current Status

Version 2 is the active approved roadmap. V2.0.1 — Architecture & Product Decisions,
V2.0.2 — Frontend Project Foundation, V2.0.3 — Design System and V2.0.4 —
Application Shell are complete. Current milestone: V2.0.5 — Market Overview &
Opportunity Scanner, implemented and verified pending
repository-owner review.

See `docs/V2_PRODUCT_DEFINITION.md`, `docs/V2_ARCHITECTURE.md` and
`docs/V2_ROADMAP.md`.

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

Milestones 4.1 and 4.2 required no migrations because they are read-only surfaces over existing tables. Milestone 4.3 adds auditable alerts in migration 016, and Milestone 4.5 adds isolated paper state in migration 017.

## Latest Verification

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

Complete repository-owner review of V2.0.5. Do not begin V2.0.6 — Symbol Research
Workspace until explicitly instructed.

Existing Version 1.0 safety boundaries remain unchanged. See `docs/NEXT_TASK.md`,
`docs/OPERATIONS_RUNBOOK.md` and `docs/RELEASE_READINESS_CHECKLIST.md`.
