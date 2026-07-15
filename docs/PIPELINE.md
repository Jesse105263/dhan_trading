# Trading Platform Pipeline

## Phase 1 (Completed)

Environment

✔ Python

✔ Dhan API

✔ Docker

✔ PostgreSQL

✔ Redis

---

## Phase 2 (Current)

Database Foundation

↓

Schema

↓

Collectors

↓

Historical Storage

---

## Phase 3

Real-Time Engine

↓

WebSocket

↓

Redis

↓

Signal Engine

↓

Alerts

---

## Phase 4

Historical Analytics

↓

Backtesting

↓

Performance

↓

Pattern Discovery

---

## Phase 5

AI Layer

↓

Claude / GPT

↓

Research

↓

Strategy Improvement

↓

Trade Explanation

---

## Phase 6

Dashboard

↓

Web UI

↓

Charts

↓

PnL

↓

Watchlists

↓

News

↓

Signals

---

## Phase 7

Production Deployment

↓

Cloud

↓

Monitoring

↓

Logging

↓

Auto Recovery

---

## Version 1.0 Operational Verification

The release verifier is downstream of committed platform state and outside both
market-data pipelines:

```text
Stable equity pipeline ─┐
                       ├── PostgreSQL ── SELECT-only release verifier
Option data pipeline ──┘
```

It does not schedule or invoke collection, analytics, alerts, Copilot or paper
trading. Operational startup, monitoring, backup and isolated recovery are defined
in `docs/OPERATIONS_RUNBOOK.md`.

## Version 3 Historical Foundation Boundary

V3.1 is not connected to either production pipeline. It exposes no downloader,
scheduled stage or continuous collection path. A future explicitly approved
historical acquisition workflow may pass licensed raw bytes to the provider-neutral
foundation; downstream consumers may read only canonical revisions and lineage.

## Version 3.2 Collection Pipeline

Persisted deterministic work is claimed in bounded batches under the existing
scheduler-lock pattern. Provider results are committed through V3.1 before an
immutable attempt outcome. Partial scope is retained, failures retry only to the
configured limit, and stale claims recover after interruption. No live provider
or production scheduler entry is enabled.

## Version 3.3 Outcome Materialization

Outcome V2 is offline downstream work: accepted canonical bars/actions flow into
a fixed-policy, fixed-`as_of` path reconstruction and then immutable outcome/path
records. It is not a continuous-collection stage and never triggers a provider.
V2 feature, similarity and opportunity pipelines remain unchanged.

## Version 3.4 Feature Materialization

Accepted V3.1 canonical bar revisions flow through a fixed-schema, fixed-`as_of`
offline query into immutable Feature Store V2 vectors and values. Histories are
bounded by both event time and availability time. The command neither collects
data nor schedules work, and the V2 feature/similarity/opportunity pipeline stays
unchanged.

## Version 3.5 Similarity Materialization

An explicit Feature Store V2 query vector and fixed cutoff select only earlier,
available vectors. Candidate-only normalization and transparent ranking complete
before eligible Outcome V2 labels are attached. This is offline derived work and
does not enter collection or the V2 opportunity pipeline.

V3.6 is an explicit offline step from one persisted Similarity V2 run to one
provisional or abstained exact-contract candidate. It never enters live pipelines.
