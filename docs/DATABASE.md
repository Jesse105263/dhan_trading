# Database Design

## Primary Database

PostgreSQL is the source of truth for persistent platform state.

## Current Core Tables

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
