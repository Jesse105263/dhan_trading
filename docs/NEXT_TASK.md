# Next Task

## Phase

Stable Market Core

## Milestone

Pipeline Failure Model

## Objective

Persist stage-level and symbol-level failures with sanitized error details and retry metadata.

## Tasks

1. Create the `pipeline_failures` migration.
2. Create a failure repository.
3. Persist failed stage names.
4. Persist sanitized exception types and messages.
5. Add retryable status.
6. Prevent credentials from appearing in errors.
7. Add failure repository tests.
8. Verify failed pipeline auditing.
9. Preserve successful pipeline behavior.

## Definition of Done

- Failed stages are persisted in PostgreSQL.
- Failure records are linked to pipeline run IDs.
- Sensitive values are excluded from stored errors.
- Retryable and non-retryable failures are distinguishable.
- Failure persistence has automated test coverage.