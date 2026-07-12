CREATE TABLE IF NOT EXISTS alert_events (
    alert_id UUID PRIMARY KEY,
    source_type VARCHAR(30) NOT NULL,
    source_id VARCHAR(100) NOT NULL,
    source_run_id VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    payload JSONB NOT NULL,
    occurred_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_alert_events_source UNIQUE (source_type, source_id),
    CONSTRAINT ck_alert_events_source_type CHECK (
        source_type IN ('SIGNAL', 'RISK_DECISION', 'PIPELINE_HEALTH')
    ),
    CONSTRAINT ck_alert_events_severity CHECK (
        severity IN ('INFO', 'WARNING', 'CRITICAL')
    )
);

CREATE INDEX IF NOT EXISTS idx_alert_events_created_at
ON alert_events(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_alert_events_source_run
ON alert_events(source_type, source_run_id);

CREATE TABLE IF NOT EXISTS alert_delivery_attempts (
    attempt_id BIGSERIAL PRIMARY KEY,
    alert_id UUID NOT NULL REFERENCES alert_events(alert_id) ON DELETE CASCADE,
    channel_name VARCHAR(60) NOT NULL,
    attempt_number INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_alert_delivery_attempt UNIQUE (alert_id, channel_name, attempt_number),
    CONSTRAINT ck_alert_delivery_status CHECK (
        status IN ('PENDING', 'DELIVERED', 'FAILED')
    ),
    CONSTRAINT ck_alert_delivery_attempt_number CHECK (attempt_number > 0),
    CONSTRAINT ck_alert_delivery_completion CHECK (
        (status = 'PENDING' AND completed_at IS NULL AND error_message IS NULL)
        OR (status = 'DELIVERED' AND completed_at IS NOT NULL AND error_message IS NULL)
        OR (status = 'FAILED' AND completed_at IS NOT NULL AND error_message IS NOT NULL)
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_alert_delivery_success
ON alert_delivery_attempts(alert_id, channel_name)
WHERE status = 'DELIVERED';

CREATE INDEX IF NOT EXISTS idx_alert_delivery_attempts_alert
ON alert_delivery_attempts(alert_id, channel_name, attempt_number DESC);
