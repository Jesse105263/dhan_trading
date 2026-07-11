# Next Task

## Milestone

Architecture Stabilization — Database Migrations

## Objective

Move database schema creation and evolution out of `services/database.py` into ordered migration files.

## Tasks

1. Create a migration runner.
2. Create a schema migrations table.
3. Split existing schema into ordered migration files.
4. Make migrations idempotent.
5. Record applied migration versions.
6. Keep `services/database.py` limited to connections.
7. Add migration tests.
8. Verify the production pipeline after migration.

## Definition of Done

- Schema changes are versioned.
- Applied migrations are recorded.
- Database initialization no longer contains the full schema.
- Existing data remains intact.
- Production pipeline behavior is unchanged.