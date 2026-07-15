# Database Design

## Primary Database

PostgreSQL is the source of truth for persistent platform state.

## Current Core Tables

### Version 3 Outcome Engine V2

Migration `025` adds immutable model policies, materialization runs, canonical
multi-horizon outcomes and ordered path lineage. It references canonical
instruments, historical bar revisions and raw manifests without modifying the V2
`historical_outcomes` table.

### Version 3 continuous collection

Migration `024` adds schedules, work items, immutable attempts, coverage gaps,
bounded repair jobs, provider quota state, quality incidents and reconciliation
results. Deterministic UUIDs and V3.1 manifest foreign keys make scheduling and
restarts auditable without changing existing Dhan or Version 2 tables.

### Version 3 historical foundation

Migration `023` adds `historical_data_sources`,
`historical_retention_policies`, exact-byte `historical_raw_payloads`, immutable
`historical_raw_manifests`, `canonical_instruments`,
`canonical_instrument_revisions`, temporal `source_instrument_mappings`,
`historical_bar_revisions`, `corporate_action_revisions` and
`historical_quality_incidents`. Canonical revisions retain raw-manifest lineage
and never overwrite historical content. Existing Version 2 evidence tables are
unchanged. See `docs/HISTORICAL_DATA_FOUNDATION.md`.

### market_events and event-context tables

Migration `022` persists canonical source-attributed events, explicit symbol and
sector labels, and leakage-classified vector, outcome, similarity and opportunity
links. It does not modify source evidence or opportunity calculations.

### trade_opportunity_runs, trade_opportunities and trade_opportunity_evidence

Migration `021` persists versioned deterministic opportunity batches,
evidence-qualified assessments and exact Similarity/Feature/Outcome lineage.
Source evidence records remain immutable.

### similarity_runs and similarity_matches

Versioned, deterministic V2.1.0 analysis records. Runs preserve query Feature
Store lineage, configuration and filters; matches preserve rank, distance,
feature diagnostics and optional Historical Outcome lineage. Migration `020`
does not modify source vectors or outcomes.

### instruments

Master list of supported underlying instruments.

### derivative_contracts

Normalized Dhan futures and option contracts.

Important expiry fields and indexes:

- `underlying_symbol`
- `instrument_type`
- `expiry`
- `is_active`
- Active underlying and expiry indexes
- Active option-chain strike index

The Expiry Repository derives available expiries directly from active rows in this table. A separate expiry table is intentionally not used because it would duplicate normalized contract state and introduce synchronization risk.

### derivative_import_runs

Security-master import lifecycle and summary counts.

### derivative_import_failures

Sanitized row-level derivative import failures.

### underlying_quotes

Persisted spot and equity quote batches.

### scanner_snapshots

Per-run market snapshots.

### market_features

Derived market features.

### pipeline_runs

Pipeline lifecycle, status and timing.

### pipeline_failures

Sanitized pipeline and stage failures.

### stage_metrics

Operational stage metrics and freshness.

### scheduler_locks

PostgreSQL-backed production-run locks.

### alert_events

One immutable, deduplicated alert per persisted source type and source ID. Stores severity, source-run lineage, human-readable content and structured JSON evidence.

### alert_delivery_attempts

Ordered per-channel delivery history with pending, delivered and failed states, timestamps and sanitized failure details. A partial unique index prevents more than one successful delivery for an alert/channel pair.

### paper_trade_orders

Simulated BUY and SELL order outcomes. Filled entries and exits are unique per signal; rejected missing-price entries remain retryable.

### paper_positions

OPEN or CLOSED simulated positions with complete signal-to-source lineage, persisted entry/latest/exit marks and gross, cost and net P&L.

### paper_trade_fills

One simulated fill per filled paper order with the exact option-chain reference run, price, fill price and transaction cost.

### paper_position_events

Immutable ordered `OPENED`, `MARKED` and `CLOSED` position transition audit.

## Planned Tables

- Option-chain runs.
- Option quotes.
- Option analytics.
- Market rankings.
- Trade signals.
- Backtests.
- Orders and positions.

## Option-Chain Collections

Migration `007_option_chain_collections.sql` adds:

- `option_chain_runs` for request lifecycle, status, selected expiry, spot price and collection counts.
- `option_chain_quotes` for normalized CE and PE snapshots by run, strike and option type.

Quotes and successful run completion are committed in one transaction. Failed runs retain sanitized error context without partial quote persistence.

## Option-Chain Analytics

Migration `008_option_chain_analytics.sql` adds `option_chain_analytics`. The table stores one deterministic analytics record per completed source run, enforced by a unique `source_run_id`. It includes ATM and straddle values, total and nearby PCR, IV summaries, OI walls, strike coverage and liquidity coverage. Deleting a source collection run cascades to its analytics.

## Option Pipeline Operational Records

Milestone 2.6 adds no schema migration. Operational runs use `pipeline_runs`, stage aggregates use `stage_metrics`, per-underlying failures use `pipeline_failures`, collections use `option_chain_runs` and `option_chain_quotes`, and analytics lineage remains enforced by `option_chain_analytics.source_run_id`.

## option_analytics_changes

Migration `009_option_analytics_changes.sql` stores deterministic differences between consecutive analytics snapshots for the same underlying and expiry. Each row preserves previous/current analytics IDs, previous/current source-run IDs, capture timestamps, elapsed time and all calculated change features. `current_analytics_id` is unique, making comparison persistence idempotent.

## Option Rankings

Migration 010 adds `option_ranking_runs` and `option_rankings`, including source analytics/change lineage, component scores, deterministic rank positions and JSON explanations.

## Option contract selections

Migration `011_option_contract_selections.sql` adds `option_contract_selection_runs` and `option_contract_selections`. Each selection retains ranking, analytics and source option-chain lineage together with liquidity, distance, spread and premium-per-lot evidence.

## Option Risk Assessments

Migration `012_option_risk_assessments.sql` adds:

- `option_risk_assessment_runs` for portfolio inputs, methodology and aggregate decision counts.
- `option_risk_assessments` for approved or rejected contracts, approved lots, quantity, exposure, maximum loss, rejection reason and lineage.

## Option Signals

Migration `013_option_signals.sql` adds `option_signal_runs` and `option_signals`. Signal rows preserve foreign-key lineage to risk assessments, selections, rankings, analytics and source option-chain runs.

## Migration 014 — Market Replay

`market_replay_runs` stores replay metadata and source signal-run lineage. `market_replay_events` stores ordered immutable replay events and compact JSON payloads.

### Option backtesting
Migration `015_option_backtesting.sql` adds `option_backtest_runs` and `option_backtest_trades`. Every trade retains signal, source-run and exit-run lineage.

## Read API Access Pattern

Milestone 4.1 adds no migration. The API reads the existing run and item tables created by migrations 010 through 015. List endpoints return newest runs first; detail endpoints return a run and its ordered child records.

## Dashboard Access Pattern

Milestone 4.2 adds no migration. Dashboard views do not connect to PostgreSQL; all persisted data crosses the existing `/api/v1` HTTP boundary.

## Alert Persistence

Migration `016_alerts.sql` adds `alert_events` and `alert_delivery_attempts`. Alert source identity is stored as text because sources span UUID-backed product records and string-backed pipeline runs. Source tables remain unchanged and alerts cannot cascade into or mutate them.

## Copilot Access Pattern

Milestone 4.4 adds no migration. The Copilot reads the existing HTTP API and does not connect to PostgreSQL or persist questions, prompts or answers.

## Paper-Trading Persistence

Migration `017_paper_trading.sql` adds isolated orders, fills, positions and audit events. Source foreign keys use `ON DELETE RESTRICT` so paper attribution cannot silently disappear. Paper persistence never updates source signals, risk decisions or option-chain marks.

## Version 1.0 Release Audit

Milestone 4.6 adds no migration. `ReleaseReadinessRepository` reads
`schema_migrations` and lineage tables without mutation. The readiness service
requires the exact ordered `001`–`017` inventory, matching filenames and SHA-256
checksums. It also checks cross-table lineage that foreign keys alone cannot prove.

Fresh migration, checksum-drift, orphan and restore tests must use a database whose
name differs from normal `POSTGRES_DB`. See `docs/OPERATIONS_RUNBOOK.md`.
## Version 2 authoritative inventory

Migrations `001`–`022` are authoritative and immutable. V2.1.4 verified exact
filesystem/applied order, filenames and SHA-256 checksums; two migration reruns
applied zero changes. Version 3 appends migrations `023`–`026` without modifying them.

Migration `026` adds `feature_schema_versions_v2`, `feature_definitions_v2`,
`feature_materialization_runs_v2`, `feature_vectors_v2` and
`feature_values_v2`. Vector/value evidence is append-only and protected by
immutability triggers. Natural uniqueness and UUIDv5 identities make the same
schema, cutoff and anchor idempotent.
