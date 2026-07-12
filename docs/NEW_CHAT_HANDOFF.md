# New Chat Handoff

## Purpose

This file is the authoritative handoff for continuing the Dhan Trading Platform in a new chat. The repository ZIP is the single source of truth. The new chat must inspect the repository and all documentation before writing code.

## Latest Verified State

- Phase 1 — Stable Market Core: complete
- Phase 2 — Option Data Platform: complete
- Phase 3 — Decision and Evaluation Platform: complete
- Milestone 4.1 — Read-Only API: complete and verified
- Milestone 4.2 — Private Read-Only Dashboard: complete and verified
- Next milestone: 4.3 — Alerts

The last committed checkpoint before the Milestone 4.1 handoff commit was:

```text
ff5a695 add option backtesting engine
```

The new chat must read the current `git log` output supplied in the prompt for the actual latest commit hash.

## Latest Verification

```text
117 tests run
OK
2 expected production-data-dependent skips
```

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

## Next Milestone

Milestone 4.3 — Alerts.

Read `docs/NEXT_TASK.md` for scope and definition of done.
