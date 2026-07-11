# Next Task

## Phase

Stable Market Core

## Milestone

Repository Contracts and Integration Tests

## Objective

Introduce explicit repository contracts and validate the PostgreSQL repositories independently from the pipeline stages.

## Tasks

1. Define repository protocols.
2. Update stages to depend on protocols.
3. Add database test helpers.
4. Add instrument repository integration tests.
5. Add underlying quote repository integration tests.
6. Add snapshot repository integration tests.
7. Add feature repository integration tests.
8. Verify transaction rollback behavior.
9. Preserve existing pipeline behavior.

## Definition of Done

- Stage dependencies use explicit repository contracts.
- Core repositories have PostgreSQL integration coverage.
- Repository transactions are independently validated.
- Production pipeline output remains unchanged.