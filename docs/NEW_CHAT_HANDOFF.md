# New Chat Handoff

## Purpose

This file is the authoritative handoff for continuing the Dhan Trading Platform in a new chat. The repository ZIP is the single source of truth. The new chat must inspect the repository and all documentation before writing code.

## Latest Approved State

- Version 2 roadmap: approved
- V2.0.1 — Architecture & Product Decisions: complete
- V2.0.2 — Frontend Project Foundation: complete
- V2.0.3 — Design System: complete
- Current milestone: V2.0.4 — Application Shell
- Current milestone state: implemented and verified pending owner review

- Phase 1 — Stable Market Core: complete
- Phase 2 — Option Data Platform: complete
- Phase 3 — Decision and Evaluation Platform: complete
- Milestone 4.1 — Read-Only API: complete and verified
- Milestone 4.2 — Private Read-Only Dashboard: complete and verified
- Milestone 4.3 — Alerts: complete and verified
- Milestone 4.4 — AI Copilot: complete and verified
- Milestone 4.5 — Paper Trading: complete and verified
- Milestone 4.6 — Version 1.0 Release Hardening: complete and approved
- Version 1.0: complete and approved

The Version 1 documentation-closure checkpoint is:

```text
555a373 close Version 1.0 documentation
```

The release-hardening implementation checkpoint is:

```text
030ade7 add release readiness verification
```

Verify the current Git state before starting any later task.

## Latest Verification

```text
176 tests run
OK
2 expected production-data-dependent skips
```

Milestone 4.6 additionally verified compileall, a 176-test standard suite, exact
migration/checksum agreement, a backup restore into `dhan_release_test_46`, fresh
application of 17 migrations with a zero-change re-run, and safe HTTP runtime
surfaces. The readiness report returned 8 PASS, 0 FAIL and 2 empty-data SKIPs on
both normal and restored state.

HTTP verification:

```text
GET /health                         -> healthy; database_ready=true
GET /api/v1                         -> resource index
GET /api/v1/rankings?limit=2        -> persisted ranking returned
GET /api/v1/signals?limit=2         -> valid empty collection
GET /api/v1/backtests?limit=2       -> valid empty collection
```

Empty signal, replay or backtest collections are valid. PostgreSQL integration tests may clean up or remove production-dependent signal-run rows. Never treat an empty list as an API defect without checking the database state.

## Important Production Facts

- Security-master rows processed: 215,940
- Derivative contracts imported: 68,406
- Rejected rows: 0
- Security-master import is idempotent
- Option underlyings are configured independently from the stable equity pipeline
- Real RELIANCE option chain collection and downstream processing have been verified

## Architectural Boundaries

- PostgreSQL is the system of record.
- Repositories perform database access only.
- Services own deterministic business policy.
- `ExpiryService` exclusively owns expiry-selection logic.
- Option analytics operate only on persisted option-chain data.
- Ranking, selection, risk and signals preserve source lineage.
- Replay and backtesting use persisted data only.
- The read API is GET-only and cannot invoke Dhan, trigger calculations or mutate state.
- LLMs never place trades.
- Stable equity and option pipelines remain separate.

## Workflow Rules

- Read the full repository ZIP and every file under `docs/` before writing code.
- Treat the repository as the single source of truth.
- Give complete files only, never snippets.
- Work on one milestone at a time.
- Run unit and PostgreSQL integration tests.
- Perform a real production verification when the milestone has a runtime surface.
- Update documentation before Git.
- Ask the user to paste command output before allowing a commit.
- Commit only after verification is green.
- Maintain backward compatibility.

## Lessons From Previous Chats

1. Do not rely on the chat summary alone. Older documentation previously reported stale phases and “verification pending,” which caused unnecessary reconstruction time.
2. Inspect `docs/NEXT_TASK.md`, `docs/PROJECT_STATUS.md`, `docs/ROADMAP.md`, `docs/DECISIONS.md`, `docs/API.md` and the relevant source/tests first.
3. Production-dependent integration tests may skip when signal runs are absent. This is expected when explicitly coded as a skip.
4. Test data must use isolated synthetic exchange/segment scopes. A prior derivative integration test accidentally deactivated production contracts because it reused production scope.
5. Never use placeholder text such as `<PASTE_ID_HERE>` literally in a shell command; obtain the ID first and substitute the actual UUID.
6. A foreground API server is not stuck. It waits for requests. Test it from a second terminal and stop it with Control+C or by killing the process bound to port 8080.
7. Verify real production commands in addition to tests; this previously caught missing-price handling in contract selection.
8. Do not claim completion until PostgreSQL tests and the production command pass.

## Dashboard Verification

- All six resource list screens returned HTTP 200 against the real local read API.
- A persisted RELIANCE ranking detail rendered summary and child records.
- A missing run rendered the expected dashboard HTTP 404 state.
- PostgreSQL-enabled suite: 128 tests, OK, 2 expected production-data-dependent skips.

Start with `python -m scripts.run_read_api` and `python -m scripts.run_dashboard`. See `docs/DASHBOARD.md`.

## Alert Verification

- PostgreSQL-enabled suite: 139 tests, OK, 2 expected production-data-dependent skips.
- A persisted RELIANCE risk approval produced an audited console alert.
- A persisted partial pipeline failure produced a warning alert.
- The current empty signal collection produced a valid zero-candidate result.
- Reprocessing the risk source reused the event and skipped its successful console delivery.

Run with `python -m scripts.generate_alerts`. See `docs/ALERTS.md`.

## Copilot Verification

- PostgreSQL-enabled suite: 155 tests, OK, 2 expected production-data-dependent skips.
- A RELIANCE ranking question returned persisted rank facts with exact API run/item lineage.
- A nonexistent symbol returned an explicit insufficient-evidence answer.
- An order-execution request was refused before retrieval or provider use.
- The optional OpenAI adapter is isolated behind a provider protocol; local synthesis remains the default.

Run with `python -m scripts.ask_copilot`. See `docs/COPILOT.md`.

## Paper-Trading Verification

- PostgreSQL-enabled suite: 163 tests, OK, 2 expected production-data-dependent skips.
- The persisted lifecycle test created BUY/SELL orders and fills, opened and closed a position, calculated realized P&L and verified complete lineage plus ordered events.
- The production CLI opened a RELIANCE paper position from a persisted signal and displayed its entry, quantity and signal ID.
- A missing newer mark produced a concise error while leaving the OPEN position unchanged.
- Verification-only paper and regenerated-signal records were removed afterward.

Run with `python -m scripts.paper_trade`. See `docs/PAPER_TRADING.md`.

## Next Activity

Review and close V2.0.4. The responsive shell, nested placeholder routes, provider
hierarchy and accessibility contract are documented in `docs/APPLICATION_SHELL.md`.

Do not begin V2.0.5 — Market Overview & Opportunity Scanner or connect the frontend
to an API without an explicit repository-owner instruction. Version 2 does not use
Milestone 4.7.

## Release-Hardening Implementation

Milestone 4.6 added a SELECT-only readiness repository and deterministic service,
exposed by `python -m scripts.verify_release`. It audits the exact migration
inventory and checksums, persisted lineage, operational state and absence of an
execution schema. Empty optional datasets are explicit `SKIP` results; invariant
violations are `FAIL` results.

Use `docs/OPERATIONS_RUNBOOK.md` for startup, shutdown, monitoring, backup and
isolated recovery. Record evidence in `docs/RELEASE_READINESS_CHECKLIST.md`.
Never run fresh-database, restore or failure-injection work against the normal
PostgreSQL database.

All Version 1.0 release verification passed, no migration `018` was required, and
the existing read-only, no-live-execution, Copilot and isolated-paper-trading
safety boundaries remain unchanged.
