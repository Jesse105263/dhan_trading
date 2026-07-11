# Dhan Trading Platform — Version 1.0 Blueprint

## 1. Product Vision

Build a production-grade Indian equities and derivatives intelligence platform that:

- Collects live and historical market data.
- Tracks the complete supported F&O universe.
- Captures equity, futures and option-chain data.
- Calculates market, volatility and derivatives features.
- Ranks trading opportunities.
- Applies liquidity, capital and risk controls.
- Generates explainable trade recommendations.
- Supports historical replay and backtesting.
- Provides a web dashboard.
- Supports AI-assisted market research.
- Keeps manual approval before order execution in Version 1.0.

The platform must improve trading decisions through data, validation and risk control.

It must not assume that any recommendation guarantees profit.

---

## 2. Version 1.0 User Experience

The user opens the platform and sees:

1. Current market state.
2. Top ranked F&O opportunities.
3. Bullish, bearish and volatility opportunities.
4. Recommended option contracts.
5. Estimated premium and capital required.
6. Stop-loss and target levels.
7. Liquidity and risk warnings.
8. Reasons behind every recommendation.
9. Historical performance of similar setups.
10. Current portfolio and exposure.
11. Alerts requiring attention.

The user can search for a symbol and see:

- Equity price history.
- Futures data.
- Current option chain.
- Historical option-chain changes.
- Implied volatility.
- Open interest.
- Put-call ratio.
- Call and put walls.
- Relative volume.
- Momentum.
- Rankings.
- Signals.
- Similar historical events.
- Backtest evidence.

---

## 3. Version 1.0 Scope

### Included

- NSE F&O equities.
- NSE indices supported by Dhan.
- Equity quote collection.
- Futures quote collection.
- Option-contract discovery.
- Option-chain collection.
- Historical snapshots.
- Feature engineering.
- Opportunity ranking.
- Risk filtering.
- Signal generation.
- Backtesting.
- Market replay.
- Dashboard.
- Alerting.
- AI explanations.
- Paper-trade tracking.
- Manual trade confirmation.

### Excluded

- Fully autonomous live trading.
- High-frequency trading.
- Tick-level order-book reconstruction.
- Colocation infrastructure.
- Guaranteed-return strategies.
- Portfolio management for external clients.
- Public multi-tenant SaaS.
- Broker support beyond Dhan.
- Regulatory reporting for managed accounts.

---

## 4. Core Architecture

```text
Dhan APIs
    │
    ├── Security Master
    ├── Equity Quotes
    ├── Futures Quotes
    ├── Option Expiries
    ├── Option Chains
    └── Orders and Positions
    │
    ▼
Collection Layer
    │
    ├── Instrument Collector
    ├── Underlying Quote Collector
    ├── Futures Collector
    ├── Option Contract Collector
    ├── Option Quote Collector
    └── Portfolio Collector
    │
    ▼
PostgreSQL / TimescaleDB
    │
    ├── Instruments
    ├── Contracts
    ├── Quotes
    ├── Snapshots
    ├── Features
    ├── Rankings
    ├── Signals
    ├── Backtests
    ├── Orders
    └── Positions
    │
    ▼
Analytics Layer
    │
    ├── Market Feature Engine
    ├── Option Analytics Engine
    ├── Ranking Engine
    ├── Risk Engine
    ├── Signal Engine
    └── Strategy Engine
    │
    ▼
Application Layer
    │
    ├── REST API
    ├── Scheduler
    ├── Alert Service
    ├── Dashboard
    ├── Backtesting UI
    └── AI Copilot