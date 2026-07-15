# Dhan Trading Platform

Institutional-grade options trading and market intelligence platform.

## Stack

- Python
- Docker
- PostgreSQL
- Redis
- Dhan API

## Setup

1. Create virtual environment
2. Install requirements

```bash
pip install -r requirements.txt
```

3. Configure `.env`

4. Start Docker

```bash
docker compose up -d
```

## Documentation

See the `docs/` folder.

Version 3 is the active approved implementation contract. It builds statistical
research and evidence depth on the completed Version 2 platform without changing
Version 2 APIs or safety boundaries. See `docs/V3_ROADMAP.md` and
`docs/V3_RESEARCH_CONTRACT.md`. The approved provider and licensing decision is
documented in `docs/V3_DATA_PROVIDER_STRATEGY.md`.
The provider-neutral raw and canonical contracts are documented in
`docs/HISTORICAL_DATA_FOUNDATION.md`.
The fixture-only continuous collection framework is documented in
`docs/CONTINUOUS_MARKET_COLLECTION.md`.
The versioned canonical Outcome Engine V2 is documented in
`docs/HISTORICAL_OUTCOME_ENGINE.md`.

## Private Dashboard

Start the read API and dashboard in separate terminals:

```bash
python -m scripts.run_read_api
python -m scripts.run_dashboard
```

Open `http://127.0.0.1:8081`. The dashboard is read-only, local by default and obtains all platform data through `/api/v1` HTTP GET requests.

## Private Alerts

Generate deduplicated, auditable alerts from persisted signals, risk decisions and pipeline health:

```bash
python -m scripts.generate_alerts
```

See `docs/ALERTS.md` for source and channel configuration.

## Private AI Copilot

With the read API running, ask a lineage-grounded research question:

```bash
python -m scripts.ask_copilot "Explain the latest ranking" --symbol RELIANCE
```

See `docs/COPILOT.md` for local and optional model-provider configuration.

## Isolated Paper Trading

Create and track simulated positions from persisted signals:

```bash
python -m scripts.paper_trade open <signal_id>
python -m scripts.paper_trade status
```

See `docs/PAPER_TRADING.md` for the complete lifecycle and safety boundary.

## Status

Version 1.0 and Version 2 are complete. V3.0 through V3.7 are committed. V3.8 —
Live Recommendation Validation is implemented pending repository-owner review.
It observes immutable shadow outcomes without execution or operational trust.

The Version 2 frontend is isolated under `frontend/`. See `docs/FRONTEND.md` for
its dependency policy and local commands, and `docs/DESIGN_SYSTEM.md` for tokens,
components and accessibility conventions.
Application-shell routing, providers and responsive layout are documented in
`docs/APPLICATION_SHELL.md`.
The first persisted Version 2 workflow is documented in `docs/MARKET_WORKSPACE.md`.
Deterministic historical matching is documented in `docs/SIMILARITY_ENGINE.md`.
Evidence-backed opportunity policy is documented in `docs/TRADE_OPPORTUNITY_ENGINE.md`.
Source-attributed event context is documented in `docs/NEWS_EVENT_INTELLIGENCE.md`.
The grounded analyst contract is documented in `docs/AI_TRADING_ANALYST.md`.
Historical evidence queries and the `/memory` workspace are documented in
`docs/MARKET_MEMORY.md`.
Versioned reusable features are documented in `docs/FEATURE_STORE.md`.
Objective post-observation ground truth is documented in
`docs/HISTORICAL_OUTCOME_ENGINE.md`.

The Version 1 SELECT-only readiness report remains available with:

```bash
python -m scripts.verify_release
```

See `docs/OPERATIONS_RUNBOOK.md` and `docs/RELEASE_READINESS_CHECKLIST.md`.
Version 2 evidence is recorded in `docs/V2_RELEASE_READINESS_CHECKLIST.md`.
Version 3 readiness starts in `docs/V3_RELEASE_READINESS_CHECKLIST.md`.
V3.7's fail-closed research boundary is documented in
`docs/CALIBRATION_RECOMMENDATION_POLICY.md`.
V3.8 shadow validation is documented in `docs/LIVE_RECOMMENDATION_VALIDATION.md`.

Run the read-only Version 3 baseline report with:

```bash
python -m scripts.benchmark_recommendations
```
