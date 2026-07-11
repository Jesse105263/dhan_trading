# Next Task

## Milestone

Production Feature Engine

## Objective

Replace the placeholder feature stage with PostgreSQL-backed feature calculation using scanner snapshot history.

## Tasks

1. Create a snapshot history query.
2. Calculate price change between runs.
3. Calculate volume change between runs.
4. Calculate relative volume using historical snapshots.
5. Persist calculated features.
6. Add feature batch validation.
7. Replace the placeholder feature stage.

## Definition of Done

- Features are calculated from PostgreSQL snapshot history.
- Feature rows are linked to a pipeline run ID.
- Feature counts match snapshot counts.
- No CSV file is required at runtime.