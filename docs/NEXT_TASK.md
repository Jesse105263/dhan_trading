# Next Task

## Phase

Phase 2 — Option Data Platform

## Milestone

Milestone 2.2 — Security Master Import

## Objective

Import and normalize Dhan derivative contracts into PostgreSQL without adding a CSV dependency to the production runtime.

## Tasks

1. Define the derivative security-master import flow.
2. Read the current Dhan security master source.
3. Filter supported NSE futures and options contracts.
4. Normalize exchange, segment, security ID and trading symbol.
5. Normalize underlying symbol, instrument type, expiry, strike and option type.
6. Normalize lot size and tick size.
7. Upsert contracts through the derivative contract repository.
8. Deactivate contracts no longer present in the latest import.
9. Persist import failures without exposing credentials or raw secrets.
10. Add validation for malformed or unsupported contracts.
11. Add import summary metrics.
12. Add unit and PostgreSQL integration tests.
13. Preserve the existing production equity pipeline and scheduler.

## Definition of Done

- Supported Dhan futures and options contracts are stored in PostgreSQL.
- Import can be rerun safely and idempotently.
- Missing contracts are deactivated without deleting historical rows.
- Malformed rows are isolated and reported.
- Contract counts and failures are visible after each import.
- No CSV file is required by the production runtime after import.
- Existing production pipeline, scheduler and derivative repository tests remain green.
