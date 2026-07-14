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

Version 2 is the active approved roadmap. It evolves the verified Version 1
backend into a polished private workspace while preserving `/api/v1`, existing
services and all no-live-execution boundaries. See `docs/V2_ROADMAP.md`,
`docs/V2_PRODUCT_DEFINITION.md` and `docs/V2_ARCHITECTURE.md`.

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

Version 1.0 is complete, verified and approved. Version 2 milestones V2.0.1 through
V2.0.8 are complete. V2.0.9 — Historical Outcome Engine is implemented pending
repository-owner review.

The Version 2 frontend is isolated under `frontend/`. See `docs/FRONTEND.md` for
its dependency policy and local commands, and `docs/DESIGN_SYSTEM.md` for tokens,
components and accessibility conventions.
Application-shell routing, providers and responsive layout are documented in
`docs/APPLICATION_SHELL.md`.
The first persisted Version 2 workflow is documented in `docs/MARKET_WORKSPACE.md`.
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
