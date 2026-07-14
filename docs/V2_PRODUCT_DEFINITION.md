# Dhan Trading Platform — Version 2 Product Definition

V2.1.0 adds deterministic historical analogue retrieval as evidence
infrastructure. Similarity is not a recommendation: it exposes reproducible
Feature Store matches, persisted outcomes, limitations and exact lineage for the
later Trade Opportunity Engine.

## Product Vision

Version 2 turns the verified Version 1 backend into a private, single-owner AI
Trading Intelligence Platform. Its primary objective is to discover statistically
exceptional opportunities from historical market behavior and eventually provide
evidence-backed entry, stop, target, confidence, historical win-rate, expected-value,
reasons-for and reasons-against evidence. It is not a generic dashboard product.

Every milestone must materially improve the system's ability to discover
statistically better opportunities. Visual or operational work that does not serve
that objective is deferred.

The primary user is one trusted repository owner operating locally first, with a
possible authenticated private VPS deployment later.

## Goals

- Provide a coherent, responsive application shell and navigation model.
- Make platform health, freshness and failures immediately understandable.
- Support opportunity discovery and searchable symbol research.
- Visualize persisted option-chain analytics and historical changes.
- Explain rankings, contract selections, risk decisions and signals with lineage.
- Visualize replay and backtest evidence without recalculation.
- Present isolated paper orders, fills, positions, events and P&L.
- Provide an evidence-grounded Copilot workspace.
- Add authenticated private access before commands or non-loopback deployment.
- Preserve backward compatibility with Version 1 pipelines and API consumers.

## Target Workflows

The final evidence chain should answer whether a current setup occurred before,
what followed, what caused failures, which entry/stop/target historically improved
expectancy, and which niche opportunities are developing. Deterministic engines
produce opportunities; the future AI analyst explains and ranks them without
inventing them.

Historical truth is a first-class product asset. Incomplete future histories stay
explicitly partial or unavailable and cannot be promoted into win-rate evidence.

1. Open the workspace and understand platform health, scheduler state, pipeline
   freshness, failures and alert history.
2. Scan ranked opportunities and filter persisted results.
3. Search for a symbol and explore its persisted market and option-chain state.
4. Follow a signal through risk, selection, ranking, analytics and source data.
5. Inspect replay timelines and backtest results, costs, drawdowns and skipped data.
6. Review paper positions and their complete audit history.
7. After authentication is implemented, explicitly open, mark or close paper
   positions through application commands.
8. Ask research questions and inspect exact Copilot evidence citations.

## Non-Goals

- Automatic or autonomous live trading.
- A Dhan broker-order adapter or live-order endpoint.
- Paper-to-live order promotion.
- LLM access to execution tools.
- Frontend access to PostgreSQL, Redis or Dhan.
- Public SaaS, enterprise multi-tenancy or public registration.
- Reimplementation of stable repositories, services or deterministic policies.
- Browser-side ranking, selection, risk, signal or backtest calculations.
- Streaming or tick-level market infrastructure without a later approved decision.

## Product Principles

- Persisted evidence is more important than visual novelty.
- Stale, missing and incomplete data must be explicit UI states.
- Financial results must show costs, assumptions and lineage.
- Read-only product workflows precede state-changing commands.
- Presentation preferences must not become trading policy.
- The application remains useful with the deterministic local Copilot provider.

## Safety Boundaries

- No automatic live execution.
- No LLM trade execution.
- No frontend-to-PostgreSQL, frontend-to-Redis or frontend-to-Dhan access.
- Frontend data crosses versioned application API boundaries.
- Repositories remain the database boundary; services retain business policy.
- Alerts cannot place orders.
- Paper trading remains isolated from live execution.
- No paper-to-live promotion path exists.
- Existing equity and option pipelines remain backward compatible.
- A live broker adapter requires a separate future roadmap decision and explicit
  repository-owner approval.
