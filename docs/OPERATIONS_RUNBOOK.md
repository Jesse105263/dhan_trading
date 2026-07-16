# Platform Operations Runbook

## Purpose

This runbook starts, monitors, stops, backs up and recovers the private Dhan
Trading Platform. PostgreSQL is the system of record. The read API, dashboard,
alerts, Copilot and paper trading are separate operational surfaces.

The commands below assume:

- Application: Dhan Trading Platform
- Folder: repository root
- Terminal: macOS `zsh`
- Virtual environment: activated project environment

Never run a recovery drill against the normal `POSTGRES_DB`. Use an explicitly
named isolated database and obtain approval before database creation, restore,
deletion or migration-ledger changes.

## Prerequisites

1. Docker Desktop is running.
2. `.env` contains PostgreSQL, Redis and Dhan settings.
3. The Python virtual environment is active.
4. Dependencies from `requirements.txt` are installed.
5. `POSTGRES_DB` identifies the normal platform database.

Confirm the intended target before every database command:

```bash
python -c "from services.config import POSTGRES_SETTINGS; print(POSTGRES_SETTINGS.dbname)"
```

## Infrastructure Startup

Start PostgreSQL and Redis:

```bash
docker compose up -d
docker compose ps
```

Test application connectivity:

```bash
python -m scripts.db_test
python -m scripts.verify_release
```

The release verifier performs SELECT-only checks. A `FAIL` is release-blocking.
A `SKIP` is acceptable only when its message says the optional persisted dataset
is empty.

For Version 2 it also audits Feature Store, Historical Outcome, Similarity,
Trade Opportunity, News/Event and Analyst grounding lineage. See
`docs/V2_RELEASE_READINESS_CHECKLIST.md`.

The Version 3 research baseline is a separate SELECT-only diagnostic:

```bash
python -m scripts.benchmark_recommendations
```

An `INSUFFICIENT` evidence state or null metric is expected when the fixed period
does not contain enough expiry-classified Version 2 outcomes. Do not treat the
report as a recommendation or run it as a substitute for release verification.

V3.1 adds no operator acquisition command. Migration `023` may be applied through
the normal migration runner, but historical tables remain empty until a separately
approved licensed import workflow exists. Do not use production collectors or
manually place downloaded files into the foundation during V3.1 review.

V3.2 adds `python -m scripts.continuous_collection` fixture-only commands. Apply
migration `024`, then use `schedule`, `execute`, `detect-gaps`,
`schedule-repairs`, `reconcile`, `status`, or `verify-idempotency`. The committed
fixture is empty. Do not configure a live adapter or external scheduler until
licensing, credentials, quotas, coverage and operations have separate approval.

V3.3 outcome materialization is an explicit offline operation over already
persisted canonical evidence:

```bash
python -m scripts.materialize_historical_outcomes_v2 --as-of <ISO_TIMESTAMP>
```

Use a fixed `--as-of` for reproducibility. An empty result is valid while licensed
history is absent. The command does not collect, call Dhan, invoke a model, alter
V2 outcomes or create a recommendation.

## Application Startup

Use separate terminals with the same virtual environment and repository folder.

Terminal 1 — read API:

```bash
python -m scripts.run_read_api
```

Terminal 2 — private dashboard:

```bash
python -m scripts.run_dashboard
```

Terminal 3 — safe health checks:

```bash
curl --fail --silent http://127.0.0.1:8080/health
curl --fail --silent http://127.0.0.1:8080/api/v1
curl --fail --silent http://127.0.0.1:8081/
python -m scripts.health_report
```

Both HTTP processes bind to loopback by default. Do not expose them publicly
without a separately reviewed authentication and deployment boundary.

## Scheduled and One-Shot Work

Stable equity and option workflows remain separate. Use the existing documented
commands; the release verifier never runs either workflow.

```bash
python -m scripts.scheduler status
python -m scripts.run_option_data_pipeline --help
```

Commands that collect market data may call Dhan. Run them only as an intentional
production operation and use the command-specific documentation in
`docs/PIPELINE.md`.

## Product Operations

Version 2 evidence materialization is explicit and idempotent:

```bash
python -m scripts.materialize_feature_store
python -m scripts.materialize_historical_outcomes
python -m scripts.materialize_similarity_run --vector-id <UUID>
python -m scripts.materialize_trade_opportunities
python -m scripts.import_news_events --file fixtures/news_events.json
python -m scripts.link_historical_events
python -m scripts.materialize_opportunity_events
python -m scripts.ask_trading_analyst --opportunity-id <UUID> --question "Explain the evidence."
```

These commands may write only their documented derived stores. They never call
Dhan, an external news provider or a model when the analyst uses its default local
provider. Do not interpret successful materialization as sufficient evidence.

Alerts persist delivery audit records and therefore are not health probes:

```bash
python -m scripts.generate_alerts
```

Copilot uses the read API and defaults to local deterministic synthesis:

```bash
python -m scripts.ask_copilot "Explain the latest ranking" --symbol RELIANCE
```

Paper trading writes only isolated paper state, but it is still a state-changing
operation and must not be used as a release health probe:

```bash
python -m scripts.paper_trade status
```

## Monitoring

At minimum, monitor:

- `GET /health` and `database_ready`.
- Latest pipeline status, completion time, failure count and stage metrics.
- Option collection completion and freshness.
- Scheduler lock status and expiry.
- Alert delivery failures and retries.
- Disk space for the PostgreSQL Docker volume and backup directory.
- Release readiness after deployments, migrations and restores.

Useful read-only commands:

```bash
python -m scripts.health_report
python -m scripts.verify_release
python -m scripts.scheduler status
```

## Graceful Shutdown

1. Stop the dashboard with Control+C.
2. Stop the read API with Control+C.
3. Allow any active one-shot pipeline to finish.
4. Confirm scheduler state.
5. Stop infrastructure only when a full platform shutdown is intended:

```bash
docker compose stop
```

Do not use `docker compose down --volumes`; it would remove persistent database
and Redis volumes.

## Backup

Create the backup directory outside the repository if needed. `pg_dump` reads the
normal database and does not change it:

```bash
mkdir -p /tmp/dhan_release_backup
docker exec dhan_postgres pg_dump -U dhan_user -d dhan_trading -Fc -f /tmp/dhan_v1.dump
docker cp dhan_postgres:/tmp/dhan_v1.dump /tmp/dhan_release_backup/dhan_v1.dump
```

Replace database/user names with the values from `.env`. Record the backup file
size and SHA-256 digest:

```bash
ls -lh /tmp/dhan_release_backup/dhan_v1.dump
shasum -a 256 /tmp/dhan_release_backup/dhan_v1.dump
```

## Isolated Restore Drill

The drill database name is `dhan_release_test_46`. It must differ from the normal
`POSTGRES_DB`. Obtain explicit approval before running any command in this section.

Create the isolated database:

```bash
docker exec dhan_postgres createdb -U dhan_user dhan_release_test_46
```

Copy and restore the backup only into that isolated database:

```bash
docker cp /tmp/dhan_release_backup/dhan_v1.dump dhan_postgres:/tmp/dhan_v1.dump
docker exec dhan_postgres pg_restore -U dhan_user -d dhan_release_test_46 --exit-on-error /tmp/dhan_v1.dump
```

Point only the current command at the isolated database and verify identity before
running tests:

```bash
POSTGRES_DB=dhan_release_test_46 python -c "from services.config import POSTGRES_SETTINGS; print(POSTGRES_SETTINGS.dbname)"
POSTGRES_DB=dhan_release_test_46 python -m scripts.verify_release
RUN_DB_INTEGRATION_TESTS=1 RELEASE_TEST_POSTGRES_DB=dhan_release_test_46 POSTGRES_DB=dhan_release_test_46 python -m unittest discover -s tests -v
```

If testing a fresh migration rather than a restored backup, create a different
empty isolated database and obtain separate approval before running the migration
runner because it creates migration metadata and schema objects:

```bash
POSTGRES_DB=dhan_release_fresh_46 python -m services.migration_runner
```

After evidence is captured, obtain approval before deleting an isolated database:

```bash
docker exec dhan_postgres dropdb -U dhan_user dhan_release_test_46
docker exec dhan_postgres dropdb -U dhan_user dhan_release_fresh_46
```

Never stop, rename, replace or delete the normal PostgreSQL database during this
drill.

The historical Version 1 drill does not by itself prove restoration of migrations
`018`–`022`. A Version 2 isolated restore/fresh-migration drill requires new,
explicit approval before `createdb`, `pg_restore`, migration execution or `dropdb`.
V2.1.4 did not perform those operations.

## Recovery Procedure

For a real recovery:

1. Stop application writers and scheduled pipelines.
2. Preserve the damaged database and logs; do not overwrite it.
3. Verify the selected backup digest and timestamp.
4. Restore into a new database, not over the existing database.
5. Point a temporary process at the recovered database.
6. Run `scripts.verify_release` and read-only HTTP smoke checks.
7. Compare critical counts and recent run IDs with pre-incident evidence.
8. Switch normal application configuration only after review and approval.
9. Retain the old database until recovery acceptance is complete.

## Incident Triage

- Migration mismatch: stop deployment; do not edit `schema_migrations` or an
  applied SQL file.
- Lineage failure: preserve records and investigate the producing service; do not
  repair rows manually.
- Read API failure: verify PostgreSQL, environment settings and `/health` logs.
- Dhan failure: allow persisted failure isolation; do not fabricate market data.
- Alert failure: retry the failed channel; successful channel deliveries remain
  suppressed.
- Copilot provider failure: use local fallback; providers have no platform tools.
- Paper transition failure: retain the current paper position; never promote it to
  a broker order.

## Release Acceptance

Complete `docs/RELEASE_READINESS_CHECKLIST.md` and
`docs/V2_RELEASE_READINESS_CHECKLIST.md`. Release acceptance requires no
failed readiness checks, green automated suites, an isolated recovery drill, clean
documentation and explicit human review.

## V3.4 Feature Store V2 Operations

Apply migration `026`, then run a fixed-cutoff offline materialization:

```bash
python -m services.migration_runner
python -m scripts.materialize_feature_store_v2 --as-of 2026-07-16T00:00:00
```

The command is safe to rerun and calls no provider. Treat a schema-checksum
mismatch, release lineage violation or unexpected missingness increase as a stop;
preserve immutable records and investigate source revisions rather than editing
feature rows. No schedule or live consumer is activated.

## V3.5 Similarity Engine V2 Operations

Run `python -m scripts.materialize_similarity_v2 --vector-id UUID` only for an
approved Feature Store V2 vector. The command is provider-free and idempotent.
Treat cutoff, lineage or readiness violations as stop conditions; never edit
immutable match evidence or promote it into an opportunity during V3.5 review.

Run `python -m scripts.materialize_opportunity_v2 --similarity-run-id UUID` only
against reviewed fixture evidence. `trusted=false` and `recommendation=false` are
fixed; abstentions and null fields must not be overridden.

## V3.7 Calibration Operations

Apply migration `029`; materialize an approved policy, then evaluate a provisional
candidate. Both commands are idempotent and have fail-closed `--fixture` paths.

## V3.8 Shadow Validation Operations

Apply migration `030`, then use the three validation commands only at explicit
cutoffs. Reruns are idempotent. Never edit snapshots or outcomes; append a later
cutoff. Treat drift suspension, missing paths and fewer than 60 shadow sessions as
non-trusted. Fixture commands call no provider or execution service.

## V3.9 Governance Operations

Apply migration `031`; register and replay reviewed immutable definitions only.
Missing shadow evidence, audit/readiness failure or any rejection stops promotion.
An offline champion role is not deployment; rollback is never automatic.
# V3.10 operator procedures

Use `scripts.v3_backfill` with `--fixture` for schedule/execute/idempotency
verification. Use `scripts.v3_operational_health` for SELECT-only backlog and
database indicators, and `scripts.verify_backup_metadata` for non-restoring
backup metadata verification. Pause, resume and stale recovery are explicit.
Never run destructive retention or `createdb`, `dropdb` or `pg_restore` without
repository-owner approval.

## Version 3 release-closure state

Version 3 is implemented and verified pending owner approval. Treat migrations
`001`–`032` as immutable and authoritative. There is no approved Version 4
roadmap. Provider activation, credentials, licensed acquisition, trusted
recommendations, live execution, retention deletion and recovery drills require
separate explicit owner authorization.

For closure verification, run the Python/frontend matrix, rerun the migration
runner expecting zero, then run the documented fixture commands and
`scripts.verify_release`. Outcome/Feature database materializers may return an
explicit empty population; Similarity fixture verification is in
`tests.test_similarity_v2` because its CLI correctly requires a persisted vector.
Never invent an identity merely to make an operator command non-empty.
