# Next Milestone

## Production Refactor

Objectives

- Refactor daily_scanner_v8.py into modular services.
- Remove duplicated logic.
- Replace CSV-based internal pipeline with PostgreSQL.
- Keep CSV export optional.
- Build production repository layer.
- Introduce scheduler.
- Begin real-time pipeline.

Expected Outcome

Scanner becomes an orchestrator using reusable engines instead of containing all business logic.