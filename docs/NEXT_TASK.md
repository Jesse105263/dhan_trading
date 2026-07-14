# Next Task

## Active Milestone

V2.1.0 — Similarity Engine.

Versioned deterministic historical matching, leakage prevention, diagnostics,
auditable materialization and GET-only similarity reads are implemented and
verified pending repository-owner review.

## Version 1.0 Status

Version 1.0 is complete and approved. Milestone 4.6 — Version 1.0 Release
Hardening is complete.

The final Version 1.0 commit checkpoint is:

```text
030ade7 add release readiness verification
```

The previous commit is:

```text
fe7c45d add isolated paper trading
```

All automated, PostgreSQL, migration, backup/restore, runtime and release-readiness
verification passed. No migration `018` was required.

## Roadmap Status

Version 2 is approved and uses `V2.0.x` numbering. See
`docs/V2_PRODUCT_DEFINITION.md`, `docs/V2_ARCHITECTURE.md` and
`docs/V2_ROADMAP.md`.

After V2.1.0 is reviewed, the next milestone is V2.1.1 — Trade Opportunity Engine.
The approved later sequence is V2.1.2 — News & Event
Intelligence and V2.1.3 — AI Trading Analyst.

## Continuing Constraints

- Treat the repository as the source of truth.
- Do not add broker-order functionality.
- Maintain backward compatibility with the production equity and option pipelines.
- Preserve the GET-only API and HTTP-only dashboard boundaries.
- Preserve Copilot execution refusal and the absence of model tools.
- Preserve isolated paper trading with no broker adapter or promotion path.
- Preserve the existing database schema and `/api/v1`.
- Do not begin V2.1.1, authentication or execution work during review.
