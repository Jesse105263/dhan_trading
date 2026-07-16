# New Chat Handoff

## Checkpoint

Final release-closure checkpoint: `<OWNER_COMMIT_AFTER_REVIEW>`.
Current implementation checkpoint: `c5f01c9 add Version 3 scale and operational hardening`.
Previous checkpoint: `874ef1f add Version 3 institutional research governance`.

Always verify a clean tree, HEAD and `origin/main` before continuing. Migrations
`001`–`032` are authoritative and applied; do not edit them. There is no migration
`033` and no approved Version 4 roadmap.

## Milestone history

Version 1 established local infrastructure, PostgreSQL/Redis, provider collection,
options data, analytics, risk/signals, replay/backtesting, read-only API/dashboard,
alerts, bounded Copilot, isolated paper trading and release hardening. Version 1
closed at `555a373` after readiness implementation `030ade7`.

Version 2 added the product architecture/frontend, market and symbol workspaces,
Market Memory, Feature Store V1, outcomes, similarity, opportunity, event
intelligence, grounded analyst and intelligence release hardening. It closed at
`ba6c0a2` and preserves `/api/v1` compatibility.

Version 3 is implemented through:

- V3.0 Research Contract — `a3ed736`
- V3.0.5 Provider Strategy — `e1c3618`
- V3.1 Historical Data Foundation — `fc20734`
- V3.2 Continuous Collection — `885883c`
- V3.3 Outcome Engine V2 — `ed0bb63`
- V3.4 Feature Store V2 — `b4c72f0`
- V3.5 Similarity Engine V2 — `fcb81a5`
- V3.6 Opportunity Engine V2 — `bb5e07b`
- V3.7 Calibration/Recommendation Policy — `254e6bf`
- V3.8 Live Recommendation Validation — `67ed31c`
- V3.9 Institutional Research Governance — `874ef1f`
- V3.10 Scale/Operational Hardening — `c5f01c9`

## Architecture

Provider-neutral immutable raw/canonical data feeds point-in-time Feature Store
V2 and Outcome V2. Similarity V2 consumes leakage-safe features/outcomes;
Opportunity V2 creates provisional exact-contract evidence; calibration applies
uncertainty and eligibility gates; shadow validation freezes and observes every
decision; offline governance controls experiments and promotion; V3.10 supplies
incremental checkpoints, durable backfills, bounded batches, health, retention
metadata and recovery controls. Existing Version 1/2 services and `/api/v1`
remain backward compatible.

## Safety boundaries

- No live provider or credential is activated.
- No Dhan/broker call, live order endpoint or paper-to-live path exists.
- Recommendation eligibility is separate from candidate ranking and operational trust.
- Live validation is shadow-only; historical evidence is immutable.
- LLMs have no execution tools; closure verification makes no LLM call.
- Retention is metadata-only; destructive retention/restore needs owner approval.
- No silent retraining, promotion, threshold change or historical rewriting.

## Verification and operator commands

```bash
python -m compileall app services scripts tests
python -m unittest discover -s tests -v
RUN_DB_INTEGRATION_TESTS=1 python -m unittest discover -s tests -v
python -m services.migration_runner
python -m scripts.verify_release
python -m scripts.benchmark_recommendations
python -m scripts.continuous_collection verify-idempotency
python -m scripts.materialize_historical_outcomes_v2 --as-of <ISO_TIMESTAMP>
python -m scripts.materialize_feature_store_v2 --as-of <ISO_TIMESTAMP>
python -m scripts.materialize_opportunity_v2 --fixture
python -m scripts.materialize_calibration_v2 --fixture
python -m scripts.materialize_recommendation_validation --fixture
python -m scripts.register_research_experiment --fixture
python -m scripts.run_offline_research --fixture
python -m scripts.evaluate_model_promotion --fixture
python -m scripts.benchmark_v3_workloads --fixture
python -m scripts.v3_operational_health
python -m scripts.verify_backup_metadata
```

Similarity, Outcome and Feature deterministic fixtures live in their unit suites;
their database commands require real persisted canonical/vector identities and
must not fabricate them. Frontend closure uses `npm run lint`, `npm test`,
`npm run build` and `npm run format:check` from `frontend/`.

## Current limitations

No licensed historical population exists. DhanHQ/TrueData and specialist-source
rights, commercial terms, credentials and budgets remain unresolved. Required
coverage targets, 20-session live collection soak, 60-session shadow validation,
populated million-scale benchmarks and an isolated recovery drill are incomplete.
No recommendation is operationally trusted and no live execution exists.

## Exact next decision and long-term objective

The next decision, only after owner approval of closure, is whether to authorize a
separate licensed-data acquisition and operational-validation programme. It is not
a software milestone and does not imply Version 4.

The long-term objective remains a private, evidence-grounded trading intelligence
platform that can produce statistically justified, calibrated, exact-contract
recommendations only after licensed population evidence, shadow validation,
governance approval and safety gates support that trust—without weakening the
no-leakage, auditability or human-approval boundaries.
