# Roadmap Index

## Active Roadmap

Version 3 is approved and active. See `docs/V3_ROADMAP.md`. V3.0 and V3.0.5 are
committed; V3.1 — Historical Data Foundation is implemented pending owner review.
Version 2 is complete and preserved in `docs/V2_ROADMAP.md`.

## Historical Version 1 Roadmap

The complete Version 1.0 architecture is documented in:

- `docs/V1_BLUEPRINT.md`

The ordered implementation plan is documented in:

- `docs/V1_IMPLEMENTATION_PLAN.md`

## Version 1.0 Status

Complete and approved.

Milestone 4.6 — Version 1.0 Release Hardening is complete. Its implementation
checkpoint is `030ade7 add release readiness verification`; the Version 1
documentation-closure checkpoint is `555a373 close Version 1.0 documentation`.

All release verification passed, and no migration `018` was required. Existing
Version 1.0 safety boundaries remain unchanged.

## Version Targets

- v0.3.0 — Stable market core
- v0.4.0 — Option data ingestion
- v0.5.0 — Option analytics
- v0.6.0 — Ranking and risk
- v0.7.0 — Signals and explainability
- v0.8.0 — Backtesting and replay
- v0.9.0 — Dashboard and alerts
- v1.0.0 — AI-assisted private trading intelligence platform

## Build Sequence

1. [x] Repository contracts
2. [x] Failure persistence
3. [x] Operational metrics
4. [x] Scheduling foundation
5. [x] Derivative contract schema
6. [x] Derivative security-master import
7. [x] Expiry repository
8. [x] Option-chain collector
9. [x] Option analytics
10. [x] Option analytics pipeline integration
11. [x] Option analytics history and change detection
12. [x] Ranking engine
13. [x] Contract selection
14. [x] Risk engine
15. [x] Signal engine
16. [x] Market replay
17. [x] Backtesting engine
18. [x] Read-only application API
19. [x] Private read-only dashboard
20. [x] Alerts
21. [x] AI Copilot
22. [x] Paper trading
23. [x] Version 1.0 release hardening verification and owner approval

## Version 1 Roadmap Boundary

The Version 1 roadmap ends with the approved Version 1.0 release. Version 2 uses
independent `V2.0.x` numbering and does not continue with Milestone 4.7.
