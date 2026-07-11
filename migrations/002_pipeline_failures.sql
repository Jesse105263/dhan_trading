CREATE TABLE IF NOT EXISTS pipeline_failures
(
    id BIGSERIAL PRIMARY KEY,
    run_id VARCHAR(36) NOT NULL,
    stage_name VARCHAR(100) NOT NULL,
    symbol VARCHAR(30),
    error_type VARCHAR(150) NOT NULL,
    error_message TEXT NOT NULL,
    retryable BOOLEAN NOT NULL DEFAULT FALSE,
    occurred_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS
idx_pipeline_failures_run_id
ON pipeline_failures(run_id);

CREATE INDEX IF NOT EXISTS
idx_pipeline_failures_occurred_at
ON pipeline_failures(occurred_at DESC);

CREATE INDEX IF NOT EXISTS
idx_pipeline_failures_retryable
ON pipeline_failures(retryable, occurred_at DESC);