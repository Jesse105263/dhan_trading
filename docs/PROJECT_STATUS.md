# Project Status

## Current Phase

Phase 4 — Product Surface

## Current Milestone

Milestone 4.3 — Alerts

## Repository Checkpoint

Milestone 4.2 is implemented and fully verified locally but intentionally uncommitted pending review. Use `git log -2 --oneline` as the source of truth for committed history.

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

Milestones 4.1 and 4.2 required no migrations because they are read-only surfaces over existing tables.

## Latest Verification

Milestone 4.2 verification completed successfully:

- Full PostgreSQL-enabled suite: 128 tests run
- Result: OK
- Expected skips: 2 production-data-dependent tests when no persisted signal run was available
- Dashboard overview and all six resource screens: HTTP 200
- Persisted RELIANCE ranking detail: HTTP 200 with summary and records
- Missing ranking run: dashboard HTTP 404 state
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

## Next Task

Milestone 4.3 — Alerts.

See `docs/NEXT_TASK.md` and `docs/NEW_CHAT_HANDOFF.md` before implementation.
