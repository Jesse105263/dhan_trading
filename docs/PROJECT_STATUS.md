# Project Status

## Current Phase

Phase 4 — Product Surface

## Current Milestone

Milestone 4.2 — Private Read-Only Dashboard

## Repository Checkpoint

Milestone 4.1 is implemented and fully verified locally. Commit the Milestone 4.1 files and this handoff documentation before creating the repository archive for the next chat.

The last committed checkpoint before Milestone 4.1 was:

- `ff5a695` — add option backtesting engine

After the handoff commit, use `git log -2 --oneline` as the source of truth for the new commit hash.

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

Milestone 4.1 required no migration because it is a read-only surface over existing tables.

## Latest Verification

Milestone 4.1 verification completed successfully:

- Full PostgreSQL-enabled suite: 117 tests run
- Result: OK
- Expected skips: 2 production-data-dependent tests when no persisted signal run was available
- `/health`: healthy with database ready
- `/api/v1`: resource index returned
- `/api/v1/rankings`: returned persisted ranking data
- `/api/v1/signals`: returned a valid empty collection
- `/api/v1/backtests`: returned a valid empty collection
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

## Next Task

Milestone 4.2 — Private Read-Only Dashboard.

See `docs/NEXT_TASK.md` and `docs/NEW_CHAT_HANDOFF.md` before implementation.
