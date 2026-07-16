# Version 3.10 — Scale and Operational Hardening

V3.10 adds operational controls around the completed Version 3 research
workloads without changing any financial formula, eligibility gate or execution
boundary. It is fixture/local-PostgreSQL only and activates no provider or
trusted recommendation.

## Incremental dependency model

The ordered stages are canonical, feature, outcome, similarity, opportunity,
calibration, validation and governance. A canonical change invalidates every
downstream stage; feature and outcome changes converge at similarity; every job
records a deterministic partition identity and each completed batch appends its
previous/current checkpoint, count and checksum. Batch size, lease, retries and
concurrency are versioned policy inputs. Failed partitions retain their last
checkpoint and remain explicit and retryable; failed dependencies suspend
downstream claims.

## Backfills, locking and recovery

`v3_backfill_jobs` is durable mutable operational state. Claims use one
transaction with `FOR UPDATE SKIP LOCKED`, bounded limits and expiring leases.
Attempts and checkpoints are immutable. Deterministic IDs suppress duplicate
schedules; dependency completion gates claims; pause/resume is explicit. Stale
leases return to `RETRYING`. Partial failure advances only the successfully
committed checkpoint. Terminal conflicts and exhausted attempts remain visible;
there is no silent repair.

```bash
python -m scripts.v3_backfill schedule --fixture
python -m scripts.v3_backfill execute --fixture
python -m scripts.v3_backfill verify-idempotency --fixture
python -m scripts.v3_operational_health
```

## Persistence and query audit

Migration `032` adds backfill jobs, immutable attempts/checkpoints, retention
metadata and targeted indexes for accepted canonical bars, feature/outcome
lookups, similarity candidates, opportunity retrieval, validation metrics,
governance registry queries and collection claims. Existing migrations and
immutable evidence tables are unchanged. Native time partition conversion is a
future owner decision after representative populated-data measurements; doing it
now would create unjustified migration and locking risk.

Bulk helpers sort deterministically, split bounded batches and keep transaction
boundaries explicit. Upserts are used only for deterministic operational
identity; immutable history uses conflict suppression plus checksum validation.

## Benchmarks

```bash
python -m scripts.benchmark_v3_workloads --fixture
python -m scripts.benchmark_v3_workloads --postgres
```

Fixture output measures a 2,000-record local ordering/batching workload and
reports elapsed time, throughput, peak-memory estimate, row and batch counts.
PostgreSQL mode reports a measured local query latency and `EXPLAIN (FORMAT
JSON)` plan. Results are machine-specific verification, not production capacity
claims. The one-million-observation objective, one-million-vector p95 target,
20-session soak, licensed backfill and live-provider reliability remain
unverified.

Checkpoint measurements on 2026-07-16: the 2,000-row fixture formed eight
250-row batches in 0.132 ms with a 34,984-byte traced peak-memory estimate. The
local PostgreSQL command measured 69.097 ms end to end; its empty-table feature
lookup plan was a sequential scan plus sort. These tiny/empty workloads cannot
validate populated index selection, throughput or production latency.

## SELECT-only health

Health reports incremental/retry backlogs, failed partitions, stale leases,
collection gaps, unresolved quarantines, database size, backup-age placeholder
and latest successful materialization. Existing component state supplies drift,
freshness and promotion evidence to release readiness. Health and backup metadata
commands perform SELECT statements only.

## Retention and recovery

Versioned metadata covers raw, canonical, derived, research, recommendation /
validation, audit and backup records. `archive_eligible` and
`destructive_action_enabled` are database-constrained false and owner approval is
required. V3.10 performs no deletion or archive.

`python -m scripts.verify_backup_metadata` verifies database identity, size and
migration inventory without creating or restoring a database. Recovery remains
the documented isolated `001`–`032` restore procedure. No `createdb`, `dropdb`,
`pg_restore` or production recovery drill was run; an isolated drill requires
explicit owner approval.

## Status and limits

V3.10 completes the implementation sequence in the Version 3 roadmap, subject to
owner review. It does not establish population-level evidence, operational trust
or production scale. Licensing, credentials, historical coverage, 60-session
shadow validation and recovery drills remain unresolved. After owner approval,
the exact next decision is whether to authorize licensed evidence acquisition and
the bounded validation/scale/recovery programme; no Version 4 roadmap is implied.
