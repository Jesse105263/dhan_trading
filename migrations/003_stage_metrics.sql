CREATE TABLE IF NOT EXISTS stage_metrics
(
    id BIGSERIAL PRIMARY KEY,
    run_id VARCHAR(36) NOT NULL,
    stage_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_ms BIGINT,
    records_requested INTEGER,
    records_received INTEGER,
    records_written INTEGER,
    source_timestamp TIMESTAMP,
    data_freshness_seconds DOUBLE PRECISION,
    created_at TIMESTAMP NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS
idx_stage_metrics_run_id
ON stage_metrics(run_id);

CREATE INDEX IF NOT EXISTS
idx_stage_metrics_stage_time
ON stage_metrics(stage_name, started_at DESC);

CREATE INDEX IF NOT EXISTS
idx_stage_metrics_status_time
ON stage_metrics(status, started_at DESC);