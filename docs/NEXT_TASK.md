# Next Task

## Milestone

Production Ranking Engine

## Objective

Replace the placeholder ranking stage with PostgreSQL-backed ranking based on persisted market features.

## Tasks

1. Create a ranking repository.
2. Normalize price-movement features.
3. Normalize relative-volume features.
4. Calculate a production market score.
5. Rank all instruments within each run.
6. Persist ranking results.
7. Validate ranking counts.
8. Replace the placeholder ranking stage.

## Definition of Done

- Every feature row receives a ranking score.
- Rankings are linked to the pipeline run ID.
- Ranking counts match feature counts.
- Ranking results are stored in PostgreSQL.
- No CSV file is required at runtime.