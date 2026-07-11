# Next Task

## Milestone

Architecture Stabilization — Repository Contracts

## Objective

Introduce explicit repository contracts and integration tests without changing production behavior.

## Tasks

1. Define repository protocols.
2. Apply dependency inversion to pipeline stages.
3. Add integration-test helpers.
4. Add PostgreSQL repository tests.
5. Verify transaction behavior.
6. Verify repository count consistency.
7. Keep the production pipeline unchanged.

## Definition of Done

- Stage dependencies are expressed through repository contracts.
- Core repositories have integration coverage.
- Database behavior is validated independently of stages.
- Production pipeline output remains unchanged.