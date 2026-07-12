# Dhan Trading Platform — Version 1.0 Implementation Plan

## Current Version

v0.3.0

## Target Version

v1.0.0

---

## Phase 1 — Stable Market Core

### Status

Complete.

### Completed

- Docker.
- PostgreSQL.
- Redis.
- GitHub.
- Environment settings.
- Structured logging.
- Migration framework.
- Pipeline run persistence.
- Instrument repository.
- F&O equity universe import.
- Equity quote collector.
- Snapshot engine.
- Basic feature engine.
- Smoke tests.
- Migration tests.

### Completed Milestones

#### Milestone 1.1 — Repository Contracts

- Define repository protocols.
- Inject contracts into stages.
- Add repository integration tests.
- Verify transaction behavior.

#### Milestone 1.2 — Pipeline Failure Model

- Create `pipeline_failures`.
- Store stage failures.
- Store symbol-level failures.
- Add retryable status.
- Sanitize exception data.

#### Milestone 1.3 — Operational Metrics

Status: Complete.

- Stage duration persisted.
- Requested, received and written counts persisted.
- Data freshness persisted.
- Health-report command added.
- Stage metrics verified across the production pipeline.

#### Milestone 1.4 — Scheduling Foundation

Status: Complete.

- Market-calendar support added.
- PostgreSQL run locking added.
- Manual and recurring scheduler commands added.
- Overlapping runs prevented.
- Stale-lock recovery added.
- Scheduler status reporting added.
- Automated scheduler tests added.

### Phase 1 Exit Criteria

- Stable migrations.
- Repository integration coverage.
- Persistent failure reporting.
- Operational metrics.
- Scheduler foundation.
- Existing production pipeline unchanged.

---

## Phase 2 — Option Data Platform

#### Milestone 2.1 — Derivative Contract Schema

Status: Complete.

- Created normalized derivative contracts table.
- Added Dhan contract identity constraints.
- Added active-contract lifecycle.
- Added expiry, strike, underlying and activity indexes.
- Added derivative contract repository contract.
- Added PostgreSQL repository implementation.
- Added model normalization and validation.
- Added unit and PostgreSQL integration tests.
- Verified the existing equity pipeline remained unchanged.

#### Milestone 2.2 — Security Master Import

Status: Complete.

- Imported supported derivative contracts.
- Added configurable symbol aliases.
- Validated lot sizes, tick sizes and contract fields.
- Deactivated missing contracts without deleting history.
- Persisted sanitized import failures and run metrics.
- Verified idempotent production import behavior.

#### Milestone 2.3 — Expiry Repository

Status: Complete.

- Added PostgreSQL expiry availability repository.
- Derived expiries from active derivative contracts.
- Centralized nearest and next expiry selection.
- Added monthly-expiry classification.
- Added days-to-expiry eligibility controls.
- Added active-expiry validation.
- Added unit and PostgreSQL integration coverage.
- Added production-data verification command.

#### Milestone 2.4 — Option-Chain Collector

Status: Next.

- Fetch one option chain.
- Normalize response.
- Persist chain run.
- Persist option quotes.
- Validate strike counts.

#### Milestone 2.5 — Universe Option Collection

- Collect all supported symbols.
- Add request throttling.
- Add retries.
- Add symbol-level failure isolation.
- Add configurable concurrency.

#### Milestone 2.6 — Option Analytics

- ATM strike.
- Total OI.
- PCR.
- Nearby PCR.
- Call wall.
- Put wall.
- Max pain.
- ATM IV.
- IV skew.
- Expected move.
- Contract liquidity.

### Phase 2 Exit Criteria

- Supported universe option chains collected.
- Failures isolated by symbol.
- Option-chain history persisted.
- Option analytics queryable.
- No CSV runtime dependency.

---

## Phase 3 — Decision Engines

#### Milestone 3.1 — Ranking Profiles

- Bullish momentum profile.
- Bearish momentum profile.
- Long-volatility profile.
- Short-volatility profile.
- Configurable weights.

#### Milestone 3.2 — Ranking Persistence

- Create market rankings table.
- Persist component scores.
- Persist final rank.
- Validate ranking count.

#### Milestone 3.3 — Contract Selection

- Select expiry.
- Select strike.
- Validate liquidity.
- Calculate premium and breakeven.
- Calculate capital requirement.

#### Milestone 3.4 — Risk Engine

- Per-trade maximum loss.
- Daily loss limit.
- Exposure limits.
- Liquidity filters.
- Spread filters.
- Expiry restrictions.

#### Milestone 3.5 — Signal Engine

- Buy call.
- Buy put.
- Bull call spread.
- Bear put spread.
- Long straddle.
- Long strangle.
- Explainability records.

### Phase 3 Exit Criteria

- Ranked opportunities persisted.
- Contract selection validated.
- Risk filters enforced.
- Explainable recommendations generated.
- No automatic trading.

---

## Phase 4 — Research and Backtesting

#### Milestone 4.1 — Strategy Definitions

- Versioned strategies.
- Parameter validation.
- Universe selection.
- Entry and exit rules.

#### Milestone 4.2 — Replay Engine

- Restore historical snapshots.
- Restore option-chain state.
- Prevent future-data access.
- Reproduce features and ranks.

#### Milestone 4.3 — Trade Simulator

- Simulated entries.
- Simulated exits.
- Stop-losses.
- Targets.
- Expiry handling.
- Slippage.
- Brokerage and taxes.

#### Milestone 4.4 — Performance Engine

- Win rate.
- Expectancy.
- Profit factor.
- Drawdown.
- Sharpe.
- Sortino.
- Regime performance.

#### Milestone 4.5 — Validation Framework

- Train-test split.
- Walk-forward analysis.
- Out-of-sample validation.
- Sensitivity testing.
- Overfitting checks.

### Phase 4 Exit Criteria

- Strategies replay historical data correctly.
- Costs and slippage included.
- No look-ahead bias.
- Results persisted and reproducible.

---

## Phase 5 — API, Dashboard and Alerts

#### Milestone 5.1 — Application API

- Health endpoint.
- Latest run endpoint.
- Rankings endpoint.
- Signals endpoint.
- Symbol detail endpoint.
- Backtest endpoint.

#### Milestone 5.2 — Market Dashboard

Status: Complete as Milestone 4.2 in the active roadmap.

- Market overview.
- Opportunity scanner.
- Rankings.
- Pipeline health.

#### Milestone 5.3 — Symbol Dashboard

- Price history.
- Features.
- Option chain.
- Option analytics.
- Signal history.

#### Milestone 5.4 — Backtesting Dashboard

- Strategy controls.
- Equity curve.
- Drawdown.
- Trade log.
- Metrics.

#### Milestone 5.5 — Alerts

Status: Complete as Milestone 4.3 in the active roadmap.

- Telegram.
- Email.
- Signal alerts.
- Risk alerts.
- Pipeline alerts.

### Phase 5 Exit Criteria

- Browser-based private dashboard.
- Searchable symbol history.
- Live recommendations visible.
- Alerts delivered reliably.

---

## Phase 6 — AI Copilot and Paper Trading

#### Milestone 6.1 — AI Data Tools

- Market query tools.
- Symbol query tools.
- Ranking explanation tools.
- Backtest explanation tools.

#### Milestone 6.2 — AI Copilot

- Explain rankings.
- Compare opportunities.
- Summarize market changes.
- Explain risk.
- Find similar historical setups.

#### Milestone 6.3 — Paper Trading

- Simulated order placement.
- Position tracking.
- P&L.
- Signal-to-trade attribution.

#### Milestone 6.4 — Manual Broker Orders

- Order preview.
- Explicit confirmation.
- Risk validation.
- Dhan order submission.
- Order audit trail.

### Phase 6 Exit Criteria

- AI answers are grounded in platform data.
- Paper trading is fully operational.
- Manual live orders require explicit approval.
- Full audit trail exists.

---

## Recommended Build Order

1. Repository contracts.
2. Failure persistence.
3. Operational metrics.
4. Scheduling foundation.
5. Derivative contract schema.
6. Security-master derivative import.
7. Expiry repository.
8. Option-chain collector.
9. Option analytics.
10. Ranking.
11. Contract selection.
12. Risk.
13. Signals.
14. Replay.
15. Backtesting.
16. API.
17. Dashboard.
18. Alerts.
19. AI Copilot.
20. Paper trading.

---

## Version Targets

### v0.3.0

Stable market core.

### v0.4.0

Option data ingestion.

### v0.5.0

Option analytics.

### v0.6.0

Ranking and risk.

### v0.7.0

Signals and explainability.

### v0.8.0

Backtesting and replay.

### v0.9.0

Dashboard and alerts.

### v1.0.0

AI-assisted private trading intelligence platform.

## Milestone 2.6 operational configuration

The dedicated option pipeline is configured through `OPTION_PIPELINE_SYMBOLS`, retry/backoff/throttle, DTE-window, nearby-strike, source-age, request-timeout, and scheduler-lock environment variables. It is intentionally not inserted into the production equity pipeline.
