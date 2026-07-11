# Next Task

## Phase

Phase 2 — Option Data Platform

## Milestone

Milestone 2.1 — Derivative Contract Schema

## Objective

Create the PostgreSQL schema and repository foundation for normalized futures and options contract metadata.

## Tasks

1. Define the derivative-contract data model.
2. Create the derivative contracts migration.
3. Store exchange, segment, security ID and trading symbol.
4. Store underlying symbol, instrument type, expiry, strike and option type.
5. Store lot size and tick size.
6. Add uniqueness constraints for Dhan contract identity.
7. Add indexes for active contracts, expiries, strikes and underlyings.
8. Add repository contracts and PostgreSQL implementation.
9. Add migration and repository tests.
10. Preserve the existing equity collection pipeline.

## Definition of Done

- Futures and options contracts can be stored without CSV runtime dependency.
- Contract identity is protected by database constraints.
- Active contracts can be queried efficiently by underlying and expiry.
- Repository behavior has automated test coverage.
- Existing production pipeline and scheduler tests remain green.
