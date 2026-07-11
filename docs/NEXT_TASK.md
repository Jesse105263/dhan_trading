# Next Task

## Milestone

Production Instrument Repository

## Objective

Replace manual instrument inserts with a production repository and load the complete supported trading universe into PostgreSQL.

## Tasks

1. Create an instrument repository.
2. Add bulk upsert support.
3. Validate exchange and security ID mappings.
4. Load the supported F&O universe.
5. Store lot size and instrument metadata.
6. Verify PostgreSQL instrument counts.
7. Remove manual seed dependencies.

## Definition of Done

- Instruments are managed through a repository.
- Bulk instrument upserts work.
- PostgreSQL contains the configured trading universe.
- Collector can request multiple instruments from PostgreSQL.
- No CSV file is required at runtime.