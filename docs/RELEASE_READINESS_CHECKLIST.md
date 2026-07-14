# Version 1.0 Release-Readiness Checklist

## Release Checkpoint

- [x] Final Version 1.0 commit recorded: `030ade7 add release readiness verification`.
- [x] Previous commit recorded: `fe7c45d add isolated paper trading`.
- [x] Release-hardening changes reviewed and committed.
- [x] `git diff --check` is clean.
- [x] No migration `018` exists; no schema defect was found.

## Automated Verification

- [x] `python -m compileall app services scripts tests` passes.
- [x] `python -m unittest discover -s tests -v` passes.
- [x] PostgreSQL-enabled suite passes against an explicitly isolated database.
- [x] Expected skips are documented and no unexpected skip hides a failure.
- [x] `python -m scripts.verify_release` has zero `FAIL` results.

Record evidence:

```text
Date/time: 2026-07-14 Asia/Kolkata
Database name: dhan_trading / dhan_release_test_46 / dhan_release_fresh_46
PASS: production/restored=8; fresh=4
FAIL: 0
SKIP: production/restored=2; fresh=6 (empty optional datasets)
Unit-test count: 176 passed; 26 opt-in database skips
PostgreSQL-test count: 176 passed; 2 expected production-data-dependent skips
```

## Migration Audit

- [x] Filesystem contains exactly migrations `001` through `017`.
- [x] Applied inventory matches the filesystem in order.
- [x] Applied filenames and SHA-256 checksums match.
- [x] Fresh isolated database migrates from zero (17 applied).
- [x] Re-running migrations on the isolated database applies zero migrations.
- [x] No migration metadata was edited for testing.
- [x] Normal PostgreSQL database was not stopped, replaced or modified by the drill.

## Lineage and State Audit

- [x] Option analytics point to matching completed collection runs.
- [x] Consecutive changes match previous/current analytics and capture order.
- [x] Rankings, selections, risk decisions and signals preserve exact lineage.
- [x] Replay and backtest audit is deterministic; current dataset is empty (`SKIP`).
- [x] Alert sources resolve to their persisted source records.
- [x] Paper lineage audit is deterministic; current dataset is empty (`SKIP`).
- [x] Terminal operational runs have consistent completion/error state.
- [x] Verification created, modified or deleted no production records.

## Safety Boundaries

- [x] Read API accepts only GET and performs no calculations or writes.
- [x] Dashboard accesses product data only through HTTP GET.
- [x] Alerts cannot call Dhan, recalculate sources or execute orders.
- [x] Copilot evidence comes only from `/api/v1`.
- [x] Copilot refuses execution requests before retrieval/provider use.
- [x] Model providers have no PostgreSQL, Dhan or execution tools.
- [x] Signal generation has no broker execution capability.
- [x] Paper state uses dedicated tables and cannot be promoted to live execution.
- [x] No live-order table, broker-order adapter or execution endpoint exists.

## Runtime Smoke Matrix

- [x] PostgreSQL and Redis report healthy.
- [x] `scripts.verify_release` completes using SELECT-only checks.
- [x] `GET /health` returns `database_ready=true`.
- [x] `GET /api/v1` returns the resource index.
- [x] Ranking list and detail return persisted lineage when data exists.
- [x] Empty signal/replay/backtest collections remain valid responses.
- [x] Dashboard overview and detail behavior pass runtime/automated verification.
- [x] Missing dashboard/API resources produce the documented 404 state.
- [x] Local Copilot returns grounded evidence or explicit insufficient evidence.
- [x] Copilot execution request is refused with zero evidence records.
- [x] Paper status is readable without creating a position.
- [x] No Dhan command was called during release-hardening verification.

## Backup and Recovery

- [x] Backup file created from the normal database using `pg_dump`.
- [x] Backup size and SHA-256 digest recorded.
- [x] Explicit approval obtained for isolated database creation.
- [x] Backup restored only into the named isolated database.
- [x] Restored database identity verified before tests.
- [x] Release verifier passes against restored data.
- [x] PostgreSQL repository/API contract tests pass against restored data.
- [ ] Explicit approval remains required before isolated database deletion; the
      Version 1.0 release approval did not authorize that separate operation.

Record evidence:

```text
Backup path: /tmp/dhan_release_backup/dhan_v1_46.dump
Backup size: 1.1 MB
SHA-256: 3521f3da04d9ba5511cfbd0431d693623e2a02639109facb7c57013de2586b73
Isolated database: dhan_release_test_46
Restore result: success
Readiness result: 8 PASS, 0 FAIL, 2 SKIP
```

## Operations and Documentation

- [x] Startup procedure works from a clean shell and activated environment.
- [x] Shutdown procedure preserves Docker volumes.
- [x] Monitoring commands are usable and read-only.
- [x] Incident and recovery steps identify when human approval is required.
- [x] Project status, architecture, decisions, database, services, pipeline,
      roadmap, handoff and changelog agree on Version 1.0 state.

## Final Approval

- [x] All verified failures resolved; Copilot live-order wording regression covered.
- [x] Verification evidence reviewed by the repository owner.
- [x] Release commit `030ade7` reviewed as the final Version 1.0 checkpoint.
- [x] Version 1.0 release approved.

No post-Version-1.0 roadmap has been approved. Roadmap planning is a separate
activity, not Milestone 4.7. Existing Version 1.0 safety boundaries remain
unchanged.
