# NEXT TASK

## Current Milestone

Database Foundation

---

## Objective

Replace CSV-first architecture with PostgreSQL-first architecture.

---

## Tasks

1.
Create production database schema.

2.
Create tables:

- instruments
- option_contract
- option_chain_snapshot
- option_quote
- underlying_quote
- trade_signal
- trade_execution
- news_event
- earnings_event
- strategy_run
- watchlist

3.

Create database initialization script.

4.

Replace CSV writes with PostgreSQL writes.

5.

Replace CSV reads with PostgreSQL reads.

---

## Definition of Done

Scanner no longer depends on CSV files.

Database becomes the single source of truth.

---

## Rules

One action at a time.

Always provide full paste-ready code.

Always specify:

- Where to run
- Folder
- Terminal
- Virtual Environment

No theory unless explicitly requested.

Update documentation after every completed milestone.
