CREATE TABLE continuous_collection_schedules (
    schedule_id UUID PRIMARY KEY, provider_code TEXT NOT NULL, dataset_type TEXT NOT NULL,
    scope JSONB NOT NULL, resolution TEXT, session TEXT NOT NULL, cadence_seconds INTEGER NOT NULL CHECK (cadence_seconds > 0),
    priority INTEGER NOT NULL, retry_policy JSONB NOT NULL, source_lineage JSONB NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE, created_at TIMESTAMP NOT NULL, UNIQUE(provider_code,dataset_type,scope,resolution,session)
);

CREATE TABLE continuous_collection_work_items (
    work_id UUID PRIMARY KEY, schedule_id UUID REFERENCES continuous_collection_schedules(schedule_id),
    repair_job_id UUID, provider_code TEXT NOT NULL, dataset_type TEXT NOT NULL, scope JSONB NOT NULL,
    requested_start TIMESTAMP, requested_end TIMESTAMP, resolution TEXT, session TEXT NOT NULL,
    priority INTEGER NOT NULL, retry_policy JSONB NOT NULL, source_lineage JSONB NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('PENDING','RUNNING','RETRYING','COMPLETED','PARTIAL','FAILED','UNAVAILABLE')),
    attempt_count INTEGER NOT NULL DEFAULT 0 CHECK(attempt_count >= 0), next_retry_at TIMESTAMP,
    terminal_failure_state TEXT, claimed_by TEXT, claimed_at TIMESTAMP, completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL, updated_at TIMESTAMP NOT NULL,
    CHECK(requested_end IS NULL OR requested_start IS NULL OR requested_end >= requested_start)
);

CREATE TABLE continuous_collection_attempts (
    attempt_id UUID PRIMARY KEY, work_id UUID NOT NULL REFERENCES continuous_collection_work_items(work_id),
    attempt_number INTEGER NOT NULL CHECK(attempt_number > 0), status TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL, completed_at TIMESTAMP, payload_manifest_id UUID REFERENCES historical_raw_manifests(manifest_id),
    succeeded_scope JSONB NOT NULL, failed_scope JSONB NOT NULL, error_type TEXT, error_message TEXT,
    retryable BOOLEAN NOT NULL, provider_metadata JSONB NOT NULL, UNIQUE(work_id,attempt_number)
);

CREATE TABLE continuous_coverage_gaps (
    gap_id UUID PRIMARY KEY, provider_code TEXT NOT NULL, dataset_type TEXT NOT NULL, instrument_id UUID REFERENCES canonical_instruments(instrument_id),
    session_date DATE NOT NULL, resolution TEXT NOT NULL, gap_type TEXT NOT NULL,
    expected_key TEXT NOT NULL, observed_key TEXT, detected_at TIMESTAMP NOT NULL,
    source_revision_id UUID, status TEXT NOT NULL CHECK(status IN ('OPEN','REPAIR_SCHEDULED','REPAIRED','QUARANTINED')),
    UNIQUE(provider_code,dataset_type,instrument_id,session_date,resolution,gap_type,expected_key)
);

CREATE TABLE continuous_repair_jobs (
    repair_job_id UUID PRIMARY KEY, gap_id UUID NOT NULL REFERENCES continuous_coverage_gaps(gap_id),
    work_id UUID REFERENCES continuous_collection_work_items(work_id), status TEXT NOT NULL,
    max_attempts INTEGER NOT NULL CHECK(max_attempts > 0), attempt_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL, completed_at TIMESTAMP, UNIQUE(gap_id)
);
ALTER TABLE continuous_collection_work_items ADD CONSTRAINT continuous_work_repair_fk FOREIGN KEY(repair_job_id) REFERENCES continuous_repair_jobs(repair_job_id);

CREATE TABLE continuous_provider_quota_state (
    provider_code TEXT PRIMARY KEY, remaining INTEGER, exhausted BOOLEAN NOT NULL,
    resets_at TIMESTAMP, throttled_until TIMESTAMP, updated_at TIMESTAMP NOT NULL,
    CHECK(remaining IS NULL OR remaining >= 0)
);

CREATE TABLE continuous_data_quality_incidents (
    incident_id UUID PRIMARY KEY, work_id UUID REFERENCES continuous_collection_work_items(work_id),
    manifest_id UUID REFERENCES historical_raw_manifests(manifest_id), incident_type TEXT NOT NULL,
    severity TEXT NOT NULL, natural_key TEXT NOT NULL, details JSONB NOT NULL,
    detected_at TIMESTAMP NOT NULL, resolved_at TIMESTAMP, UNIQUE(incident_type,natural_key,manifest_id)
);

CREATE TABLE continuous_reconciliation_results (
    reconciliation_id UUID PRIMARY KEY, work_id UUID REFERENCES continuous_collection_work_items(work_id),
    manifest_id UUID REFERENCES historical_raw_manifests(manifest_id), result_type TEXT NOT NULL,
    source_revision_id UUID, canonical_revision_id UUID, conflict_incident_id UUID,
    checksum_valid BOOLEAN NOT NULL, details JSONB NOT NULL, reconciled_at TIMESTAMP NOT NULL,
    UNIQUE(work_id,manifest_id,result_type,canonical_revision_id)
);

CREATE INDEX continuous_work_pending_idx ON continuous_collection_work_items(status,next_retry_at,priority,created_at);
CREATE INDEX continuous_gap_status_idx ON continuous_coverage_gaps(status,session_date);
CREATE INDEX continuous_attempt_work_idx ON continuous_collection_attempts(work_id,attempt_number);

CREATE FUNCTION reject_continuous_attempt_update() RETURNS trigger AS $$ BEGIN RAISE EXCEPTION 'collection attempts are immutable'; END; $$ LANGUAGE plpgsql;
CREATE TRIGGER continuous_attempt_immutable BEFORE UPDATE OR DELETE ON continuous_collection_attempts FOR EACH ROW EXECUTE FUNCTION reject_continuous_attempt_update();
