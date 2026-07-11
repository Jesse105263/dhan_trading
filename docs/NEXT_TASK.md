# Next Task

## Milestone

Production Snapshot Repository

## Objective

Replace the placeholder snapshot stage with PostgreSQL-backed quote retrieval and scanner snapshot persistence.

## Tasks

1. Create an underlying quote repository.
2. Load the latest quote batch from PostgreSQL.
3. Create a scanner snapshot repository.
4. Persist snapshot records in PostgreSQL.
5. Add batch-level validation.
6. Add snapshot execution metrics.
7. Remove the placeholder snapshot stage.

## Definition of Done

- Latest underlying quotes are loaded through a repository.
- Snapshot records are persisted in PostgreSQL.
- The production pipeline contains a real snapshot stage.
- No CSV file is required at runtime.