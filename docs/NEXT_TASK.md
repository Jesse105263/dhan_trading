# Next Task

## Phase

Phase 4 — Product Surface

## Milestone

Milestone 4.6 — Version 1.0 Release Hardening

## Objective

Validate the complete Version 1.0 platform, audit all safety boundaries and produce an operational release runbook.

## Implementation State

The SELECT-only readiness verifier, focused tests, operational runbook and release
checklist are implemented locally. The automated, PostgreSQL, runtime, fresh
migration and isolated recovery verification matrix is green. Remaining work is
owner review and release approval. No migration `018` was required.

## Required Scope

- Run complete end-to-end production and recovery verification.
- Audit database migrations, source lineage and cleanup behavior.
- Audit read-only, alert, AI and paper/live-execution safety boundaries.
- Document startup, shutdown, monitoring, backup and recovery procedures.
- Resolve stale documentation and produce a release-readiness checklist.

## Engineering Constraints

- Treat the repository and verified production state as the source of truth.
- Do not add broker-order functionality.
- Maintain backward compatibility with the production equity and option pipelines.
- Add unit tests and integration/smoke coverage appropriate to the selected implementation.
- Update documentation before Git.
- Commit only after full verification.

## Definition of Done

- All platform milestones pass the complete verification matrix.
- Safety and recovery audits have explicit evidence.
- The operational runbook is usable from a clean environment.
- Existing automated and PostgreSQL integration suites remain green.
- Documentation reflects the final architecture and operating commands.
