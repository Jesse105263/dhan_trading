# Next Task

## Phase

Stable Market Core

## Milestone

Operational Metrics

## Objective

Persist pipeline and stage-level operational metrics for monitoring, diagnosis and future dashboards.

## Tasks

1. Create stage metrics migration.
2. Persist stage start and completion times.
3. Persist stage duration.
4. Persist records requested.
5. Persist records received.
6. Persist records written.
7. Persist data freshness.
8. Add metrics repository tests.
9. Add health-report command.
10. Preserve current pipeline behavior.

## Definition of Done

- Every production stage records operational metrics.
- Pipeline runs expose record counts and duration.
- Data freshness is queryable.
- Metrics are covered by tests.
- Production behavior remains unchanged.