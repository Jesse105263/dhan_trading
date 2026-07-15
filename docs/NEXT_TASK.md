# Next Task

V3.0 is committed at `a3ed736`; V3.0.5 is committed at `e1c3618`. V3.1 —
Historical Data Foundation is implemented and awaiting repository-owner review.
Do not start provider acquisition or V3.2.

Historical provider acquisition remains blocked until written DhanHQ and TrueData
licensing confirmation, dated quotes, coverage samples, NSE/BSE specialist terms,
approved news scope, budget and storage/backup capacity are recorded. See
`docs/V3_DATA_PROVIDER_STRATEGY.md`.

The current baseline command is read-only:

```bash
python -m scripts.benchmark_recommendations
```

It must not be interpreted as a recommendation or as statistically sufficient
evidence.

## Preserved Version 2 handoff

## Final Version 2 Milestone

V2.1.4 — Intelligence Release Hardening & Handoff.

Expanded SELECT-only readiness, complete automated/runtime verification, operator
idempotency, safety audit and release handoff are implemented and verified pending
repository-owner review.

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

Version 3 is approved. V3.1 is the active review milestone. Its raw/canonical
foundation uses local deterministic tests only; historical coverage remains empty.

## Continuing Constraints

- Treat the repository as the source of truth.
- Do not add broker-order functionality.
- Maintain backward compatibility with the production equity and option pipelines.
- Preserve the GET-only `/api/v1` boundary; V2 analyst POST routes remain bounded,
  research-only application commands with no persistence or execution access.
- Preserve Copilot execution refusal and the absence of model tools.
- Preserve isolated paper trading with no broker adapter or promotion path.
- Preserve the existing database schema and `/api/v1`.
- Do not begin a new implementation roadmap, authentication or execution work
  during review.
