# Version 2 Intelligence Release-Readiness Checklist

## Checkpoint and scope

- [x] Implementation checkpoint: `1a7d189 add Version 2 AI trading analyst`.
- [x] Previous checkpoint: `f0abefb add Version 2 news and event intelligence`.
- [x] V2.1.4 changes are staged separately for owner review.
- [x] No product feature, dependency, migration or Version 3 roadmap was added.

## Automated verification

- [x] Compileall passed.
- [x] Standard suite: 240 tests passed; 36 expected database-gated skips.
- [x] PostgreSQL suite: 240 tests passed; 5 expected data-dependent skips.
- [x] Frontend lint passed.
- [x] Frontend tests: 39 passed.
- [x] Frontend build and formatting checks passed.

## Migration audit

- [x] Exactly migrations `001`–`022` exist; no migration `023` exists.
- [x] Applied versions and filenames match in exact order.
- [x] Applied SHA-256 checksums match the filesystem.
- [x] Two normal-database reruns applied zero migrations.
- [x] No applied migration file or ledger record was modified.

## Expanded SELECT-only readiness

- [x] Database, migration, Version 1 lineage and operational checks passed.
- [x] Feature Store lineage passed: 9 audited, 0 violations.
- [x] Historical Outcome lineage passed: 9 audited, 0 violations.
- [x] Similarity lineage and future-leakage audit passed: 9 audited, 0 violations.
- [x] Trade Opportunity lineage and insufficient-field audit passed: 1 audited, 0 violations.
- [x] News/Event lineage and publication-time audit passed: 1 audited, 0 violations.
- [x] Analyst evidence grounding passed: 1 audited, 0 violations.
- [x] Execution-schema boundary passed: 1 audited, 0 violations.
- [x] Final result: 14 PASS, 0 FAIL, 2 acceptable empty-data SKIP.

The verifier remains SELECT-only. Source tests separately prove that analyst
execution requests refuse before evidence/provider access and that product
boundaries do not import broker, Dhan, database or paper-promotion capabilities.

## Runtime smoke

- [x] `/health`, `/api/v1`, V2 overview and scanner returned HTTP 200.
- [x] Symbol Intelligence, Market Memory, Features and Outcomes returned HTTP 200.
- [x] Similarity, Trade Opportunities and Events returned HTTP 200.
- [x] Local Analyst explanation returned HTTP 200 and `INSUFFICIENT_EVIDENCE`.
- [x] Analyst execution request returned `REFUSED` with safety-boundary provider.
- [x] All implemented frontend workspace routes returned HTTP 200 on loopback.

## Operator idempotency and current evidence

- [x] Feature Store ran twice: 9 sources / 9 vectors each time.
- [x] Historical Outcomes ran twice: 9 sources / 9 outcomes each time.
- [x] Similarity ran twice with the same deterministic ID: 8 matches, insufficient.
- [x] Trade Opportunities ran twice with the same deterministic ID: 1 record, 0 eligible.
- [x] Fixture event import ran twice: 2 source records / 2 events.
- [x] Historical event linking ran twice: 0 time-window links.
- [x] Opportunity-event context ran twice: 1 context link.
- [x] Local Analyst CLI returned grounded insufficient evidence; no model call occurred.

There are zero classified expiry outcomes. The platform must not claim statistically
reliable recommendations until sufficient classified history exists.

## Safety and recovery

- [x] No live-order table, broker adapter or execution endpoint exists.
- [x] No paper-to-live path, LLM execution tool or browser database/Dhan access exists.
- [x] Similarity inputs exclude outcomes; publication-time gates prevent event leakage.
- [x] Non-eligible opportunities retain null entry, stop, target, win-rate and EV fields.
- [x] Version 1 backup/restore evidence remains recorded and unchanged.
- [ ] A new isolated Version 2 restore drill was not authorized or performed. It
      requires explicit approval for database creation, restore, migration and deletion.

## Owner review

- [ ] Review staged V2.1.4 changes.
- [ ] Record the final V2.1.4 commit checkpoint after commit.
- [ ] Approve Version 2 core intelligence release closure.

After approval, the next activity is a separate roadmap and data-acquisition
planning session. No Version 3 roadmap is approved.
