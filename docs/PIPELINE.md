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
