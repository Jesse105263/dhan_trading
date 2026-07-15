# CHANGELOG

---

## 2026-07-16

### V3.6 — Opportunity Engine V2

- Added migration `028` for immutable policies, runs, exact-contract candidates
  and evidence lineage.
- Added option-path-only levels, net expected value, effective sample size,
  concentration, liquidity/fill and distribution abstention.
- Preserved null unsupported outputs and all V2/recommendation safety boundaries.

### V3.5 — Similarity Engine V2

- Added migration `027` with immutable similarity policies, runs and matches.
- Added three transparent distance models, configurable feature/family weights,
  point-in-time normalization, filtering, ranking, diagnostics and quality.
- Added strict candidate and outcome cutoffs, explicit insufficient evidence,
  release auditing, unit and PostgreSQL coverage without changing V2 consumers.

### V3.4 — Feature Store V2

- Added migration `026` with immutable versioned feature definitions,
  materialization runs, canonical vectors, values, quality metrics and lineage.
- Added deterministic point-in-time features across eight evidence-backed
  families with explicit missing and normalization policies.
- Added offline materialization, release auditing, unit and PostgreSQL coverage
  while preserving V2 consumers and recommendation logic.

### V3.3 — Outcome Engine V2

- Added migration `025` with immutable outcome policies, runs, multi-horizon
  canonical outcomes and exact ordered bar/manifest lineage.
- Added underlying/option duration, session and expiry paths with explicit
  missingness, corporate-action abstention, costs, barriers, MFE/MAE, drawdown,
  volatility adjustment, expectancy and payoff ratio.
- Added deterministic offline materialization, point-in-time revision selection,
  readiness auditing, unit and PostgreSQL coverage.
- Preserved V2 Outcome, Similarity, Opportunity, Analyst and recommendation logic.

## 2026-07-15

### V3.2 — Continuous Market Collection

- Added migration `024` for deterministic schedules/work, immutable attempts,
  coverage gaps, repair jobs, provider quota state, incidents and reconciliation.
- Added session/expiry policy, bounded claims and retries, restart recovery,
  partial success, fixture ingestion through V3.1, gap detection and health.
- Added fixture-only operator commands plus unit and PostgreSQL coverage.
- Added no live adapter, credential, external call, production schedule, Dhan
  behavior change, recommendation or execution path.

### V3.1 — Historical Data Foundation

- Added migration `023` with immutable raw payload/manifests, source and retention
  metadata, stable canonical instruments, temporal provider mappings, revised
  historical bars, revised corporate actions and quality incidents.
- Added provider-neutral frozen contracts, a bounded local-only JSON adapter,
  deterministic exact-byte/canonical checksums, UUIDv5 identities, validation,
  deduplication, revision and cross-source quarantine policy.
- Extended SELECT-only readiness with historical-foundation lineage checks and
  added comprehensive unit and PostgreSQL integration coverage.
- Added no live provider adapter, credential, download, backfill, scheduler,
  continuous collector, API, frontend, recommendation or execution path.

### V3.0 — Research Contract and Benchmark Baseline

- Recorded the approved Version 3 roadmap as the implementation contract.
- Added checksummed `v3-research-contract-v1` with fixed research periods,
  purge/embargo controls and minimum evidence policy.
- Added deterministic always-long, random-control, momentum, mean-reversion,
  Version 2 ranking and Version 2 opportunity baselines.
- Added SELECT-only population, coverage, abstention, win-rate, return, drawdown
  and Brier reporting with explicit insufficient evidence and null unsupported
  metrics.
- Added CLI, unit and PostgreSQL integration coverage without a migration, API,
  dependency, provider, model, recommendation, frontend or execution change.

---

## 2026-07-05

### Infrastructure

- Installed Docker Desktop
- Verified Docker installation
- Verified Docker Compose
- Ran first Docker container

### Containers

Created:

- PostgreSQL container
- Redis container

Containers verified running.

### Python Environment

Installed:

- psycopg
- python-dotenv

Created:

- .env

### Database

Successfully connected Python to PostgreSQL.

Verified:

- Connection
- Table creation
- Insert
- Select
- Close connection

### Project

Official transition from script-based development to platform architecture.

## 2026-07-11

### Infrastructure

- Docker installed
- PostgreSQL configured
- Redis configured
- Git initialized
- Project reorganized
- Documentation centralized

### Services Added

- config.py
- database.py
- collector.py
- feature_engine.py
- ranking_engine.py
- risk_engine.py
- signal_engine.py
- snapshot_engine.py

### Database

- PostgreSQL connectivity established
- Initial schema created

## 2026-07-11

### Market Data Collection

- Added PostgreSQL-backed instrument configuration.
- Added production Dhan quote collector.
- Added live market quote ingestion from Dhan.
- Added batch persistence into `underlying_quotes`.
- Added collector execution metrics.
- Verified MCX equity collection using security ID `31181`.
- Verified DhanHQ Python client version `2.2.0`.
- Removed CSV dependency from the production collector path.

## 2026-07-11

### Instrument Repository

- Added production PostgreSQL instrument repository.
- Added bulk instrument upsert support.
- Added schema migration support for instrument metadata.
- Added `tick_size` support to the `instruments` table.
- Added F&O equity universe importer.
- Excluded NSE test and mock instruments.
- Imported 209 production F&O equities.
- Stored security IDs, lot sizes, tick sizes and exchange segments.
- Updated the collector to load instruments through the repository.
- Added multi-instrument Dhan quote collection.
- Verified 209 of 209 live quotes were collected and persisted.
- Confirmed zero missing instruments in the latest collection batch.

## 2026-07-11

### Snapshot Engine

- Added UUID-based pipeline run IDs.
- Added pipeline run status and timing metadata.
- Added PostgreSQL `pipeline_runs` table.
- Added underlying quote repository.
- Added scanner snapshot repository.
- Replaced the placeholder snapshot stage.
- Added latest quote batch retrieval.
- Added source quote timestamp validation.
- Added snapshot batch persistence.
- Added per-run snapshot count validation.
- Persisted 209 snapshots for the verified production universe.
- Added snapshot auditability by run ID.

## 2026-07-11

### Feature Engine

- Added PostgreSQL `market_features` table.
- Added production feature repository.
- Replaced the placeholder feature stage.
- Added previous-run price lookup.
- Added previous-run volume lookup.
- Added price change calculation.
- Added price change percentage calculation.
- Added volume change calculation.
- Added volume change percentage calculation.
- Added rolling average prior volume.
- Added relative-volume calculation.
- Added configurable 20-run history window.
- Added per-run feature persistence and validation.
- Verified 209 feature rows for 209 production instruments.
- Verified full snapshot-to-feature count consistency.

## 2026-07-11

### Architecture Stabilization

- Added centralized application settings.
- Added environment-driven pipeline configuration.
- Added structured application logging.
- Replaced stage lifecycle prints with structured logs.
- Added pipeline run repository.
- Added persistent pipeline success and failure states.
- Added configurable Dhan request timeout.
- Added configurable Dhan batch size.
- Added configurable feature lookback window.
- Added automated pipeline smoke tests.
- Verified successful pipeline completion persistence.
- Verified failed pipeline persistence.

## 2026-07-11

### Database Migration Framework

- Added ordered SQL migration files.
- Added `schema_migrations` table.
- Added migration version tracking.
- Added SHA-256 checksum validation.
- Added protection against modifying applied migrations.
- Added duplicate migration version validation.
- Added transactional migration execution.
- Moved schema management out of `services/database.py`.
- Reduced `services/database.py` to connection management.
- Added automated migration discovery tests.
- Added migration checksum tests.
- Added duplicate-version tests.
- Verified migration idempotency.
- Verified existing production data remained intact.

## 2026-07-11

### Repository Contracts and Integration Tests

- Added explicit repository protocols.
- Applied dependency inversion to the snapshot engine.
- Applied dependency inversion to the feature engine.
- Added snapshot insert-count validation.
- Added feature upsert-count validation.
- Added PostgreSQL instrument repository integration test.
- Added PostgreSQL underlying quote repository integration test.
- Added PostgreSQL snapshot repository integration test.
- Added PostgreSQL feature repository integration test.
- Added automatic integration-test cleanup.
- Verified no test data remained after execution.
- Verified production pipeline behavior remained unchanged.

## 2026-07-11

### Pipeline Failure Model

- Added `pipeline_failures` migration.
- Added PostgreSQL failure repository.
- Added failed-stage tracking.
- Added sanitized error persistence.
- Added retryable failure classification.
- Added symbol-level failure support.
- Added access-token, client-ID, password and JWT redaction.
- Added failure persistence to the pipeline.
- Added error sanitizer unit tests.
- Added pipeline failure smoke tests.
- Verified successful runs create zero failure records.

## 2026-07-11

### Operational Metrics

- Added `stage_metrics` database migration.
- Added PostgreSQL stage metrics repository.
- Added per-stage success and failure metrics.
- Added stage start and completion timestamps.
- Added stage duration measurement.
- Added records-requested metrics.
- Added records-received metrics.
- Added records-written metrics.
- Added source-data freshness measurement.
- Added metrics for Database, Collector, Snapshot Engine and Feature Engine.
- Added metrics support for future Ranking, Risk and Signal stages.
- Added production health-report command.
- Added stage-metrics smoke-test coverage.
- Verified seven stage metrics for a successful pipeline run.
- Verified 209 requested, received and written records across production data stages.

## 2026-07-12

### Scheduling Foundation

- Added configurable Indian market timezone and session hours.
- Added weekday, market-hours and exchange-holiday validation.
- Added PostgreSQL-backed scheduler locks.
- Added overlap prevention for recurring production runs.
- Added stale-lock recovery through lock expiry.
- Added manual calendar override while preserving lock safety.
- Added scheduler status reporting.
- Added one-shot and recurring scheduler commands.
- Preserved direct production pipeline execution through `run_pipeline.py`.
- Added scheduler unit tests covering market gating, overlap prevention, stale locks and failure cleanup.
- Added `004_scheduler_foundation.sql` migration.
- Verified all 24 automated tests pass, with 3 opt-in PostgreSQL integration tests skipped by default.
- Verified the seven-stage production pipeline completes successfully.
- Verified scheduler locks are released after execution and failure.
- Verified scheduler lock acquisition and automatic release using PostgreSQL.

## 2026-07-12

### Derivative Contract Schema

- Added `005_derivative_contracts.sql`.
- Added normalized PostgreSQL storage for futures and options contract metadata.
- Added immutable Dhan contract identity using exchange segment and security ID.
- Added trading symbol, underlying symbol, instrument type, expiry, strike and option type fields.
- Added lot size and tick size validation.
- Added active-contract lifecycle fields.
- Added database constraints for supported instrument and option types.
- Added database constraints for valid option and futures field combinations.
- Added indexes for active contracts, underlyings, expiries and strikes.
- Added derivative contract repository protocol.
- Added PostgreSQL derivative contract repository.
- Added normalization and validation for derivative contract models.
- Added active-contract, expiry and option-chain query support.
- Added contract deactivation support.
- Added repository unit tests.
- Added PostgreSQL integration tests covering upserts, queries and deactivation.
- Verified 31 automated tests pass, with 5 opt-in integration tests skipped by default.
- Verified all 5 PostgreSQL integration tests pass when enabled.
- Verified the existing seven-stage production pipeline remains green.

## 2026-07-12

### Expiry Repository and Service

- Added PostgreSQL-backed expiry availability queries derived from active derivative contracts.
- Added active contract counts per underlying, instrument type and expiry.
- Added centralized expiry selection for nearest, next and monthly expiries.
- Added minimum and maximum days-to-expiry eligibility controls.
- Added active-expiry validation and explicit not-found errors.
- Added a repository protocol for expiry data access.
- Added comprehensive expiry-service unit tests.
- Added opt-in PostgreSQL expiry repository integration tests.
- Added a production-data expiry verification command.
- Preserved the existing derivative-contract expiry query for backward compatibility.
- Added no database migration because `derivative_contracts` remains the normalized source of truth.

## 2026-07-12

### Option-Chain Collector

- Added `007_option_chain_collections.sql`.
- Added transactional option-chain run and quote persistence.
- Added PostgreSQL underlying identity resolution.
- Added centralized collector orchestration using `ExpiryService` exclusively.
- Added Dhan option-chain HTTP client.
- Added normalized option-chain request, response and quote models.
- Added complete CE/PE strike validation.
- Added sanitized failed-run persistence.
- Added command-line collection entry point.
- Added collector unit tests and PostgreSQL repository integration coverage.
- Preserved the production equity pipeline and scheduler.

## Milestone 2.5 — Option Analytics

- Added deterministic analytics models and service.
- Added completed option-chain run reader and idempotent analytics persistence.
- Added ATM, straddle, PCR, IV, OI-wall, strike-distance and liquidity-coverage calculations.
- Added stale and incomplete source-chain rejection.
- Added unit and PostgreSQL integration coverage.

## Milestone 2.6 — Option Analytics Pipeline Integration

- Added configurable multi-underlying option collection and analytics stages.
- Added bounded retry, linear backoff, request throttling, and per-underlying failure isolation.
- Added aggregate stage metrics and source-run lineage preservation.
- Added a scheduler-safe one-shot option pipeline command with a dedicated lock.
- Added unit and PostgreSQL integration coverage.
- Preserved the production equity pipeline unchanged.

## 2026-07-12 — Milestone 2.7

### Option Analytics History and Change Detection

- Added ordered historical analytics retrieval by underlying and expiry.
- Added consecutive-snapshot resolution with explicit source lineage.
- Added deterministic OI, PCR, IV, ATM straddle, wall, price and liquidity changes.
- Added persisted option analytics change records with idempotent current-snapshot identity.
- Added validation for incomparable, duplicate and unordered snapshots.
- Added unit and PostgreSQL integration tests.
- Added production comparison command.

## Milestone 3.1 — Ranking Engine

- Added deterministic, explainable option ranking with persisted lineage.
- Added liquidity, activity, volatility and directional component scores.
- Added unit and PostgreSQL integration coverage plus production verification.

## Milestone 3.2 — Contract Selection

- Added deterministic contract selection from persisted ranking runs.
- Added liquidity, distance, spread, expiry-age and premium-per-lot constraints.
- Added source-run, analytics and ranking lineage for every selected contract.
- Added unit and PostgreSQL integration coverage plus a production CLI.

## Milestone 3.3 — Risk Engine

- Added portfolio-aware long-option risk assessment.
- Added deterministic lot sizing under available-capital, per-trade loss, total exposure and underlying concentration limits.
- Added persisted approvals and rejections with complete selection lineage and explanations.
- Added unit tests, PostgreSQL integration coverage and a production verification command.

## Milestone 3.4 — Signal Engine

- Added deterministic signals generated only from risk-approved option contracts.
- Added explicit action, direction, strategy context, entry reference, confidence, approved size and maximum-loss fields.
- Added full risk, selection, ranking, analytics and source-run lineage.
- Added long-call, long-put and paired long-straddle-leg classification.
- Added unit tests, PostgreSQL integration coverage and a production verification command.

## Milestone 3.5 — Market Replay

- Added immutable persisted-lineage market replay runs and events.
- Added deterministic event sequencing from option-chain capture through signal generation.
- Added lineage validation and strict no-live-API replay boundary.
- Added unit and PostgreSQL integration coverage plus production replay CLI.

## Milestone 3.6 — Backtesting
- Added deterministic backtesting of persisted option signals against subsequent persisted option-chain marks.
- Added configurable target, stop-loss, slippage and transaction-cost assumptions.
- Added persisted trade-level lineage and run-level P&L, return, win-rate, profit-factor and drawdown metrics.

## Milestone 4.1 — Read-Only API

- Added a stable versioned GET-only application API.
- Added list and detail endpoints for rankings, selections, risk assessments, signals, replay runs and backtests.
- Added bounded pagination input, UUID validation, structured errors and deterministic JSON serialization.
- Added unit and PostgreSQL integration coverage.
- Added a private WSGI server command without introducing live-trading capabilities.

## 2026-07-12

### Option Platform Completion Through Milestone 4.1

- Added derivative contract schema and idempotent Dhan security-master import.
- Imported 68,406 eligible derivative contracts from 215,940 rows with zero rejected rows.
- Added centralized expiry repository and service.
- Added transactional option-chain collection and real Dhan production verification.
- Added deterministic option analytics, historical change detection and lineage.
- Added ranking engine, contract selection, portfolio-aware long-option risk engine and explainable signal generation.
- Added persisted market replay and deterministic backtesting with slippage and transaction costs.
- Added versioned GET-only read API under `/api/v1`.
- Added health, ranking, selection, risk, signal, replay and backtest resources.
- Preserved the no-execution boundary and backward compatibility with the stable equity pipeline.
- Expanded the PostgreSQL-enabled automated suite to 117 tests, all passing with two expected production-data-dependent skips.
- Added authoritative new-chat handoff documentation for continuation at Milestone 4.2.

## Milestone 4.2 — Private Read-Only Dashboard

- Added a private, loopback-bound dashboard server with no new dependency.
- Added an HTTP-only client for the existing `/health` and `/api/v1` GET contract.
- Added overview, ranking, selection, risk, signal, replay and backtest screens.
- Added run-detail tables, structured evidence rendering and replay timelines.
- Added stable empty, unavailable, invalid-response and not-found states.
- Added no-cache, anti-framing and restrictive content-security response headers.
- Added comprehensive `unittest` coverage and real API-to-dashboard runtime verification.
- Added no database migration, write endpoint, Dhan call or execution capability.

## Milestone 4.3 — Alerts

- Added persisted signal, risk-decision and pipeline-health alert generation.
- Added deterministic source identity and database-enforced event deduplication.
- Added per-channel delivery attempts with ordered status and sanitized failure audit.
- Added successful-delivery suppression and failed-delivery retry behavior.
- Added local console and configurable private-webhook delivery adapters.
- Added migration `016_alerts.sql`, an operational CLI and comprehensive unit/integration coverage.
- Verified real persisted risk and pipeline alerts plus valid empty-signal behavior.
- Preserved the no-Dhan, no-recalculation and no-order-execution boundaries.

## Milestone 4.4 — AI Copilot

- Added a private research Copilot consuming only the stable `/api/v1` HTTP contract.
- Added question-aware evidence selection for rankings, selections, risk, signals and backtests.
- Added symbol filtering and verified run/item lineage citations.
- Added deterministic local synthesis and an optional provider interface.
- Added an OpenAI Responses API adapter with no tools or write authority.
- Added explicit insufficient-evidence, provider-failure fallback and execution-refusal behavior.
- Added API-key sanitization to the shared error boundary.
- Added comprehensive unit and PostgreSQL-backed API-contract integration coverage.
- Added no migration, database access, Dhan call or order capability.

## Milestone 4.5 — Paper Trading

- Added isolated simulated BUY/SELL orders, fills, positions and ordered audit events.
- Added full signal, risk, selection, ranking, analytics and source-market lineage.
- Added deterministic persisted-mark entry, marking and close transitions.
- Added configurable slippage and transaction costs with unrealized and realized P&L.
- Added retryable missing-entry-price rejections and non-destructive invalid-transition errors.
- Added position status and P&L reporting CLI.
- Added migration `017_paper_trading.sql` plus comprehensive unit and PostgreSQL integration coverage.
- Added no Dhan call, broker adapter, live-order endpoint or paper-to-live promotion path.

## Milestone 4.6 — Version 1.0 Release Hardening

- Added a SELECT-only release-readiness repository.
- Added deterministic PASS, FAIL and SKIP release checks.
- Added exact migration `001`–`017` inventory, filename and checksum auditing.
- Added option, decision, evaluation, alert and paper lineage audits.
- Added operational-state and execution-schema boundary checks.
- Added a release-verification CLI with release-blocking exit status.
- Added focused unit and explicitly isolated PostgreSQL integration coverage.
- Added the Version 1.0 operations runbook and release-readiness checklist.
- Closed a verified Copilot execution-intent gap for live-order and broker-order
  wording while preserving refusal before evidence retrieval.
- Added no migration, Dhan call, broker adapter or production cleanup behavior.

## Version 1.0 Release Closure

- Version 1.0 was reviewed and approved by the repository owner.
- Recorded `030ade7 add release readiness verification` as the final Version 1.0
  commit checkpoint and `fe7c45d add isolated paper trading` as its predecessor.
- Confirmed all automated, PostgreSQL, migration, backup/restore, runtime and
  release-readiness verification passed.
- Confirmed no migration `018` was required.
- Closed Milestone 4.6 — Version 1.0 Release Hardening.
- Preserved all existing Version 1.0 safety boundaries.
- Recorded that no post-Version-1.0 roadmap is approved; the next activity is a
  separate roadmap-planning exercise, not Milestone 4.7.

## V2.0.2 — Frontend Project Foundation

- Added an isolated React, TypeScript and Vite project under `frontend/`.
- Added npm lockfile, strict TypeScript projects, ESLint and Prettier configuration.
- Added Vitest and Testing Library coverage for the placeholder, environment
  validation and native-fetch API client abstraction.
- Added a single placeholder route rendering only the platform name and Version 2.
- Added loopback-only development serving and production build configuration.
- Added browser-safe environment handling and optional development proxy settings.
- Added no API calls, product workspaces, charts, authentication or business logic.
- Preserved `/api/v1`, Python services, repositories, migrations and database state.

## V2.0.3 — Design System

- Added semantic light and future-dark theme tokens for color, typography,
  spacing, shape, elevation, breakpoints, z-index and motion.
- Added global focus, disabled, reduced-motion, layout and responsive styles.
- Added reusable controls, content surfaces, status labels, loading/error/empty
  states, headers, toolbar, modal, drawer and typed table shell.
- Added native form semantics with associated hints and validation errors.
- Added sticky responsive tables with sortable-header request UI but no sorting
  policy or data behavior.
- Added `lucide-react` as the single tree-shakeable SVG icon source.
- Added component behavior and accessibility tests.
- Added no product workspace, API, authentication, chart or business logic.

## V2.0.4 — Application Shell

- Added a responsive header, navigation rail, nested main-content outlet and status
  footer using the Version 2 design system.
- Added data-free placeholder routes for Home, Market Overview, Scanner, Symbol
  Research, Signals, Replay & Backtesting, Paper Portfolio, Operations, Copilot and
  Settings, plus an in-shell not-found route.
- Added fixed-theme, shell-state, render-error and loading providers with UI-only
  modal, drawer and toast hosts.
- Added keyboard-visible navigation, semantic landmarks, a skip link and accessible
  mobile navigation controls.
- Added desktop, compact-tablet and mobile navigation behavior without animation or
  business state.
- Added tests for nested routing, shell landmarks, responsive navigation controls,
  provider hosts, placeholder statuses and error/loading boundaries.
- Added no API request, authentication, chart, product data or business behavior.

## V2.0.5 — Market Overview & Opportunity Scanner

- Added purpose-built GET-only V2 overview, opportunity-list and detail projections
  while preserving `/api/v1`.
- Added deterministic freshness bands and structured query, unavailable and
  not-found errors.
- Added dense persisted overview and scanner workspaces with filters, sorting,
  source timestamps, downstream availability and lineage navigation.
- Added no migration, dependency, write route, pipeline trigger or execution path.

## V2.0.6 — Symbol Intelligence Workspace

- Added bounded symbol search and expiry-aware persisted intelligence projections.
- Added analytics/ranking history, selection, risk, signals, timeline and lineage.
- Added two-symbol comparison and related-expiry navigation without chart libraries.
- Explicitly marks unsupported IV percentile, Greeks and risk score as unpersisted.
- Added no dependency, migration, pipeline change or execution capability.

## V2.0.7 — Feature Store & Market Memory Foundation

- Added SELECT-only canonical snapshot and feature-history projections over
  existing persisted option analytics and ranking lineage.
- Added latest, previous, range, detail, allow-listed feature-history and exact
  two-snapshot comparison routes under `/api/v2/memory`.
- Added the accessible `/memory` workspace with filters, bounded history, stale and
  empty/error states, CSS/SVG evolution, and two-snapshot comparison.
- Added unit, API, PostgreSQL repository and frontend coverage.
- Added `docs/MARKET_MEMORY.md`; no migration, dependency, collector, pipeline,
  recommendation or execution capability was added.
## V2.0.8 — Feature Store

- Added migration `018` for versioned feature vectors and normalized numeric values.
- Added 56 explicit analytics, change, ranking and temporal feature definitions.
- Added idempotent, bounded offline materialization with exact Market Memory lineage
  and explicit completeness metadata.
- Added GET-only feature definition, list and detail routes under `/api/v2/features`.
- Added unit, API and PostgreSQL integration coverage without AI, recommendation,
  collector, frontend or execution behavior.
## V2.0.9 — Historical Outcome Engine

- Added migration `019` for versioned objective outcomes with exact feature,
  analytics, ranking and terminal-vector lineage.
- Added deterministic, restartable materialization with explicit unavailable,
  partial and expiry-complete states.
- Added observed return, MFE, MAE, peak gain/loss, holding duration, expiry outcome
  and win/loss fields without interpolation or prediction.
- Added GET-only outcome list, detail, history and persisted-only statistics APIs.
- Added unit, API and PostgreSQL integration coverage; no frontend, AI,
  recommendation or execution behavior was added.

## V2.1.0 — Similarity Engine

- Added migration `020` for deterministic, versioned similarity runs and matches.
- Added historical-only normalized weighted distance with explicit allow-list,
  weights, null policy, overlap threshold, diagnostics and leakage prevention.
- Added GET-only model, analysis and persisted-run APIs plus an idempotent operator
  materializer and exact Feature/Outcome lineage.
- Added a focused accessible Market Memory similarity view with explicit
  insufficient-evidence behavior and no recommendation language.
- Added service, API, PostgreSQL integration and frontend coverage without new
  dependencies, collectors, AI, execution or `/api/v1` changes.

## V2.1.1 — Trade Opportunity Engine

- Added migration `021` for versioned opportunity runs, assessments and exact
  Similarity/Feature/Outcome evidence links.
- Added deterministic evidence eligibility, long underlying reference zones,
  expected value, historical win rate, evidence quality, risk/reward, scoring and ranking.
- Added explicit `INSUFFICIENT_EVIDENCE` and `NO_OPPORTUNITY` states with null
  unsupported recommendation fields.
- Added GET-only list/detail APIs and accessible opportunity workspace/detail routes.
- Added backend, PostgreSQL and frontend coverage without AI, Dhan, execution,
  paper trading, alerts, new dependencies or `/api/v1` changes.

## V2.1.2 — News & Event Intelligence

- Added migration `022` for canonical events and exact vector, outcome, similarity
  and opportunity context lineage.
- Added bounded idempotent local JSON ingestion with deterministic identity,
  checksum, sanitization, deduplication and no external calls.
- Added exact-symbol/market-wide relevance, publication-time leakage gates,
  historical holding/expiry context and context-only opportunity attachments.
- Added GET-only event/context APIs, event timeline and opportunity risk panels.
- Added backend, PostgreSQL and frontend tests without AI, sentiment, Dhan,
  execution, paper writes, alerts, dependencies or `/api/v1` changes.

## V2.1.3 — AI Trading Analyst

- Added versioned application-assembled evidence over the complete deterministic
  intelligence chain with exact citations and missing-data markers.
- Added local explanation and comparison, pre-retrieval refusal and sanitized
  optional-provider fallback without response persistence.
- Added bounded POST research commands, operator CLI and accessible analyst
  workspace with refusal and insufficient-evidence states.
- Added no migration, dependency, execution tool, opportunity calculation,
  external verification call or `/api/v1` contract change.

## V2.1.4 — Intelligence Release Hardening & Handoff

- Expanded the SELECT-only readiness audit across the full Version 2 intelligence
  lineage, future-data gates, insufficient fields and analyst grounding.
- Verified all Python/PostgreSQL/frontend suites, migrations `001`–`022`, loopback
  API/workspace routes and deterministic operator idempotency.
- Recorded limited local evidence and prohibited statistical-reliability claims
  until classified expiry outcomes exist.
- Added the Version 2 readiness checklist and safe continuation handoff without a
  migration, dependency, product feature, external call or Version 3 roadmap.

## V3.0.5 — Data Provider & Licensing Strategy

- Compared Dhan, exchange products, India-focused vendors, broker APIs and
  enterprise/international providers using official public sources.
- Selected DhanHQ for historical data and live backup and TrueData for continuous
  collection, subject to written licensing and coverage confirmation.
- Defined authoritative corporate-action, announcement, news and macro sources;
  a provider-neutral canonical boundary; source/revision/conflict policy; raw
  manifests; licensing metadata; storage estimates; cost envelopes; and V3.1
  entry gates.
- Added documentation only: no provider was contacted, purchased, configured or
  called, and no migration, credential, dependency, collector or executable
  behavior changed.
