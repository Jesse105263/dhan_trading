CREATE TABLE IF NOT EXISTS derivative_import_runs
(
    run_id UUID PRIMARY KEY,
    status VARCHAR(20) NOT NULL,
    source_url TEXT,
    source_file_name VARCHAR(255),
    source_timestamp TIMESTAMP,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    rows_read INTEGER NOT NULL DEFAULT 0,
    rows_eligible INTEGER NOT NULL DEFAULT 0,
    contracts_upserted INTEGER NOT NULL DEFAULT 0,
    contracts_deactivated INTEGER NOT NULL DEFAULT 0,
    rows_rejected INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,

    CONSTRAINT ck_derivative_import_runs_status
        CHECK (status IN ('RUNNING', 'COMPLETED', 'FAILED')),

    CONSTRAINT ck_derivative_import_runs_non_negative_counts
        CHECK (
            rows_read >= 0
            AND rows_eligible >= 0
            AND contracts_upserted >= 0
            AND contracts_deactivated >= 0
            AND rows_rejected >= 0
        )
);

CREATE INDEX IF NOT EXISTS idx_derivative_import_runs_started_at
ON derivative_import_runs(started_at DESC);

CREATE TABLE IF NOT EXISTS derivative_import_failures
(
    id BIGSERIAL PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES derivative_import_runs(run_id) ON DELETE CASCADE,
    row_number INTEGER,
    security_id VARCHAR(30),
    trading_symbol VARCHAR(120),
    error_type VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    occurred_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_derivative_import_failures_run_id
ON derivative_import_failures(run_id, id);
