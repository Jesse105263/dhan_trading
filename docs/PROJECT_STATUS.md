# Project Status

## Current Phase

Phase 4 — Product Surface

## Current Milestone

Milestone 4.6 — Version 1.0 Release Hardening

## Repository Checkpoint

Milestone 4.5 is implemented and verified locally but intentionally uncommitted pending review. The latest committed checkpoint is `7e4abe9 add grounded private ai copilot`.

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

Milestone 4.5 verification completed successfully:

- Full PostgreSQL-enabled suite: 163 tests run
- Result: OK
- Expected skips: 2 production-data-dependent tests when no persisted signal run was available
- RELIANCE paper entry: filled BUY order, BUY fill and OPEN position with exact signal lineage
- Missing newer mark: concise error and unchanged OPEN position
- Persisted runtime audit: OPENED event with entry price, costs and net P&L
- Verification-only paper and signal records cleaned after the runtime check
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

## Next Task

Milestone 4.6 — Version 1.0 Release Hardening.

See `docs/NEXT_TASK.md` and `docs/NEW_CHAT_HANDOFF.md` before implementation.
