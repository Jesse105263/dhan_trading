# Version 3.2 Continuous Market Collection

## Scope and safety

V3.2 adds a provider-neutral, restartable continuous-collection framework above
the V3.1 raw/canonical foundation. The only executable provider is
`LocalFixtureCollectionProvider`, which accepts bounded local JSON bytes and has
no HTTP, credential or broker capability. No live schedule is enabled and the
existing Dhan equity and option collectors are unchanged.

TrueData and Dhan remain procurement selections only. Activation requires written
retention/derived-use/model-use/backup terms, an approved secret boundary,
measured quotas and coverage, a reviewed adapter, and an explicit production
change. Unknown licensing fails closed.

## Policy and work lifecycle

`ContinuousCollectionPolicy` classifies explicit Asia/Kolkata timestamps as
`PRE_OPEN`, `REGULAR`, `CLOSE`, `POST_CLOSE`, or `NON_TRADING`. Weekends and an
explicit holiday set never schedule market-session datasets. Expiry dates are
explicit inputs. Post-close is the reconciliation/repair window; late payloads
retain their actual availability time through V3.1.

Work supports instrument masters, underlying/index/futures/option bars,
option-chain and supported quote/depth snapshots, corporate actions, and events or
announcements. UUIDv5 identity covers provider, dataset, sorted scope, range,
resolution, session and repair lineage. Each record stores priority, bounded
exponential retry policy, source lineage, timestamps, status, attempts, next retry
and terminal failure.

Statuses are `PENDING`, `RUNNING`, `RETRYING`, `COMPLETED`, `PARTIAL`, `FAILED`,
and `UNAVAILABLE`. Claims use `FOR UPDATE SKIP LOCKED`; stale running work returns
to retry after a bounded lease. The scheduler adapter uses the existing
PostgreSQL `continuous-market-collection` lock. Concurrency is bounded by claim
limit. Missing adapters become explicit terminal attempts; no failure is silent.

## Persistence and lineage

Migration `024_continuous_market_collection.sql` adds schedules, work items,
immutable attempts, coverage gaps, repair jobs, provider quota state, continuous
quality incidents and reconciliation results. Attempts retain successful/failed
scope, failure type/message, provider metadata and raw-manifest lineage.

Successful payloads pass unchanged into `HistoricalDataService`; V3.1 therefore
owns exact-byte SHA-256 manifests, raw deduplication, canonical checksums,
same-source revisions, availability timestamps, cross-source quarantine and the
no-destructive-overwrite guarantee. Partial success commits its successful payload
and records failed scope for bounded follow-up.

## Gaps, repair, and reconciliation

Gap detection compares explicit expected session intervals with accepted current
canonical bars. Deterministic IDs preserve the original absence. The schema also
supports missing sessions, symbol coverage, expiries, contracts and stale
revisions; expectations must come from authoritative inputs and are never
fabricated. One bounded repair job is allowed per gap. Repair reuses canonical
deduplication, and conflicts remain quarantined.

Late and revised payloads use the V3.1 path: exact replay is deduplicated,
same-source content appends a superseding revision, and differing cross-source
bars remain quarantined. V3.2 does not invent an automatic cross-source winner;
canonical-source priority requires an approved live-source policy.

## Health and commands

Read-only status reports scheduled, completed, failed, retrying and stale work,
quota exhaustion, missing intervals, repair backlog and unresolved conflicts. The
schema supports throttling, collection lag, coverage, abnormal row counts, clock
drift and checksum incidents when a future adapter supplies those measurements.
`/api/v1` is unchanged.

Fixture-only commands are safe to rerun:

```bash
python -m scripts.continuous_collection schedule
python -m scripts.continuous_collection execute
python -m scripts.continuous_collection detect-gaps
python -m scripts.continuous_collection schedule-repairs
python -m scripts.continuous_collection reconcile
python -m scripts.continuous_collection status
python -m scripts.continuous_collection verify-idempotency
```

The fixture is deliberately empty; it verifies workflow without fabricating a
market observation. Gap and reconciliation commands report zero unless an
explicit deterministic expectation or late fixture exists.

## Limitations

There is no live adapter, daemon, cron entry, provider credential, full exchange
holiday source, entitlement, licensed dataset or production cadence. Persisted
schedules are infrastructure, not activated production jobs. V3.3 remains Outcome
Engine V2.

## V3.3 downstream boundary

Outcome Engine V2 consumes only canonical revisions already committed through
V3.1/V3.2. It never schedules collection or repairs and cannot activate a
provider. A late revision affects only a later explicit outcome `as_of` run.
