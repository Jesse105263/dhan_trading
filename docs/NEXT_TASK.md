# Next Task

## Active Milestone

V2.0.6 — Symbol Intelligence Workspace.

The persisted overview, filterable latest-ranking scanner and lineage detail are
implemented and verified pending repository-owner review. They are GET-only.

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

After V2.0.6 is reviewed, the next milestone is V2.0.7 — Signals & Decision Lineage.

## Continuing Constraints

- Treat the repository as the source of truth.
- Do not add broker-order functionality.
- Maintain backward compatibility with the production equity and option pipelines.
- Preserve the GET-only API and HTTP-only dashboard boundaries.
- Preserve Copilot execution refusal and the absence of model tools.
- Preserve isolated paper trading with no broker adapter or promotion path.
- Preserve the existing database schema and `/api/v1`.
- Do not begin V2.0.7, authentication or execution work during review.
