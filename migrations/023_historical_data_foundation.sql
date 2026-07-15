CREATE TABLE historical_data_sources (
    source_id UUID PRIMARY KEY,
    provider_code TEXT NOT NULL,
    product_code TEXT NOT NULL,
    dataset_code TEXT NOT NULL,
    source_kind TEXT NOT NULL CHECK (source_kind IN ('PROVIDER','EXCHANGE','REGULATOR','LOCAL_FIXTURE')),
    source_reference TEXT,
    created_at TIMESTAMP NOT NULL,
    UNIQUE (provider_code, product_code, dataset_code)
);

CREATE TABLE historical_retention_policies (
    policy_id UUID PRIMARY KEY,
    source_id UUID NOT NULL REFERENCES historical_data_sources(source_id),
    agreement_id TEXT NOT NULL,
    agreement_version TEXT NOT NULL,
    use_class TEXT NOT NULL,
    raw_retention TEXT NOT NULL CHECK (raw_retention IN ('ALLOWED','DENIED','UNKNOWN')),
    normalized_retention TEXT NOT NULL CHECK (normalized_retention IN ('ALLOWED','DENIED','UNKNOWN')),
    derived_data TEXT NOT NULL CHECK (derived_data IN ('ALLOWED','DENIED','UNKNOWN')),
    model_training TEXT NOT NULL CHECK (model_training IN ('ALLOWED','DENIED','UNKNOWN')),
    backup_copy TEXT NOT NULL CHECK (backup_copy IN ('ALLOWED','DENIED','UNKNOWN')),
    post_termination TEXT NOT NULL CHECK (post_termination IN ('ALLOWED','DENIED','UNKNOWN')),
    redistribution TEXT NOT NULL CHECK (redistribution IN ('ALLOWED','DENIED','UNKNOWN')),
    retention_until TIMESTAMP,
    deletion_obligation TEXT,
    effective_from TIMESTAMP NOT NULL,
    effective_to TIMESTAMP,
    created_at TIMESTAMP NOT NULL,
    CHECK (effective_to IS NULL OR effective_to > effective_from),
    UNIQUE (source_id, agreement_id, agreement_version)
);

CREATE TABLE historical_raw_payloads (
    payload_id UUID PRIMARY KEY,
    source_id UUID NOT NULL REFERENCES historical_data_sources(source_id),
    policy_id UUID NOT NULL REFERENCES historical_retention_policies(policy_id),
    payload_checksum TEXT NOT NULL CHECK (length(payload_checksum) = 64),
    payload_bytes BYTEA NOT NULL,
    byte_count BIGINT NOT NULL CHECK (byte_count >= 0),
    content_type TEXT NOT NULL,
    received_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL,
    UNIQUE (source_id, payload_checksum)
);

CREATE TABLE historical_raw_manifests (
    manifest_id UUID PRIMARY KEY,
    payload_id UUID NOT NULL REFERENCES historical_raw_payloads(payload_id),
    source_id UUID NOT NULL REFERENCES historical_data_sources(source_id),
    policy_id UUID NOT NULL REFERENCES historical_retention_policies(policy_id),
    external_batch_id TEXT NOT NULL,
    provider_schema_version TEXT NOT NULL,
    adapter_version TEXT NOT NULL,
    request_metadata JSONB NOT NULL,
    page_number INTEGER NOT NULL CHECK (page_number > 0),
    retry_number INTEGER NOT NULL CHECK (retry_number >= 0),
    coverage_start TIMESTAMP,
    coverage_end TIMESTAMP,
    record_count INTEGER NOT NULL CHECK (record_count >= 0),
    payload_checksum TEXT NOT NULL CHECK (length(payload_checksum) = 64),
    canonical_checksum TEXT NOT NULL CHECK (length(canonical_checksum) = 64),
    manifest_checksum TEXT NOT NULL CHECK (length(manifest_checksum) = 64),
    parent_manifest_id UUID REFERENCES historical_raw_manifests(manifest_id),
    captured_at TIMESTAMP NOT NULL,
    ingested_at TIMESTAMP NOT NULL,
    CHECK (coverage_end IS NULL OR coverage_start IS NULL OR coverage_end >= coverage_start),
    UNIQUE (source_id, external_batch_id, payload_checksum)
);

CREATE TABLE canonical_instruments (
    instrument_id UUID PRIMARY KEY,
    identity_key TEXT NOT NULL UNIQUE,
    instrument_class TEXT NOT NULL CHECK (instrument_class IN ('EQUITY','INDEX','FUTURE','OPTION')),
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE canonical_instrument_revisions (
    revision_id UUID PRIMARY KEY,
    instrument_id UUID NOT NULL REFERENCES canonical_instruments(instrument_id),
    manifest_id UUID NOT NULL REFERENCES historical_raw_manifests(manifest_id),
    revision_number INTEGER NOT NULL CHECK (revision_number > 0),
    record_checksum TEXT NOT NULL CHECK (length(record_checksum) = 64),
    is_current BOOLEAN NOT NULL,
    supersedes_revision_id UUID REFERENCES canonical_instrument_revisions(revision_id),
    exchange TEXT NOT NULL,
    segment TEXT NOT NULL,
    trading_symbol TEXT NOT NULL,
    underlying_instrument_id UUID REFERENCES canonical_instruments(instrument_id),
    isin TEXT,
    expiry DATE,
    strike NUMERIC,
    option_type TEXT CHECK (option_type IS NULL OR option_type IN ('CE','PE')),
    lot_size INTEGER,
    tick_size NUMERIC,
    valid_from TIMESTAMP NOT NULL,
    valid_to TIMESTAMP,
    available_at TIMESTAMP NOT NULL,
    ingested_at TIMESTAMP NOT NULL,
    CHECK (valid_to IS NULL OR valid_to > valid_from),
    CHECK (lot_size IS NULL OR lot_size > 0),
    CHECK (tick_size IS NULL OR tick_size > 0),
    CHECK (strike IS NULL OR strike >= 0),
    UNIQUE (instrument_id, revision_number),
    UNIQUE (instrument_id, record_checksum)
);

CREATE UNIQUE INDEX canonical_instrument_current_idx
ON canonical_instrument_revisions(instrument_id) WHERE is_current;

CREATE TABLE source_instrument_mappings (
    mapping_id UUID PRIMARY KEY,
    source_id UUID NOT NULL REFERENCES historical_data_sources(source_id),
    instrument_id UUID NOT NULL REFERENCES canonical_instruments(instrument_id),
    manifest_id UUID NOT NULL REFERENCES historical_raw_manifests(manifest_id),
    provider_security_id TEXT NOT NULL,
    provider_symbol TEXT NOT NULL,
    provider_exchange TEXT NOT NULL,
    provider_segment TEXT NOT NULL,
    valid_from TIMESTAMP NOT NULL,
    valid_to TIMESTAMP,
    mapping_checksum TEXT NOT NULL CHECK (length(mapping_checksum) = 64),
    discovered_at TIMESTAMP NOT NULL,
    CHECK (valid_to IS NULL OR valid_to > valid_from),
    UNIQUE (source_id, provider_exchange, provider_segment, provider_security_id, valid_from),
    UNIQUE (source_id, mapping_checksum)
);

CREATE TABLE historical_bar_revisions (
    bar_revision_id UUID PRIMARY KEY,
    instrument_id UUID NOT NULL REFERENCES canonical_instruments(instrument_id),
    manifest_id UUID NOT NULL REFERENCES historical_raw_manifests(manifest_id),
    interval_code TEXT NOT NULL,
    bar_open_at TIMESTAMP NOT NULL,
    bar_close_at TIMESTAMP NOT NULL,
    session_date DATE NOT NULL,
    adjustment_state TEXT NOT NULL CHECK (adjustment_state IN ('RAW','SPLIT_ADJUSTED','TOTAL_RETURN_ADJUSTED')),
    revision_number INTEGER NOT NULL CHECK (revision_number > 0),
    record_checksum TEXT NOT NULL CHECK (length(record_checksum) = 64),
    is_current BOOLEAN NOT NULL,
    acceptance_state TEXT NOT NULL CHECK (acceptance_state IN ('ACCEPTED','QUARANTINED')),
    supersedes_revision_id UUID REFERENCES historical_bar_revisions(bar_revision_id),
    open_price NUMERIC NOT NULL CHECK (open_price >= 0),
    high_price NUMERIC NOT NULL CHECK (high_price >= 0),
    low_price NUMERIC NOT NULL CHECK (low_price >= 0),
    close_price NUMERIC NOT NULL CHECK (close_price >= 0),
    volume NUMERIC CHECK (volume IS NULL OR volume >= 0),
    open_interest NUMERIC CHECK (open_interest IS NULL OR open_interest >= 0),
    trade_count BIGINT CHECK (trade_count IS NULL OR trade_count >= 0),
    bid_price NUMERIC CHECK (bid_price IS NULL OR bid_price >= 0),
    ask_price NUMERIC CHECK (ask_price IS NULL OR ask_price >= 0),
    event_at TIMESTAMP NOT NULL,
    provider_at TIMESTAMP,
    available_at TIMESTAMP NOT NULL,
    ingested_at TIMESTAMP NOT NULL,
    CHECK (bar_close_at > bar_open_at),
    CHECK (high_price >= GREATEST(open_price, close_price, low_price)),
    CHECK (low_price <= LEAST(open_price, close_price, high_price)),
    CHECK (ask_price IS NULL OR bid_price IS NULL OR ask_price >= bid_price),
    UNIQUE (instrument_id, interval_code, bar_open_at, adjustment_state, revision_number),
    UNIQUE (instrument_id, interval_code, bar_open_at, adjustment_state, record_checksum)
);

CREATE UNIQUE INDEX historical_bar_current_idx
ON historical_bar_revisions(instrument_id, interval_code, bar_open_at, adjustment_state)
WHERE is_current AND acceptance_state = 'ACCEPTED';

CREATE TABLE corporate_action_revisions (
    action_revision_id UUID PRIMARY KEY,
    action_identity TEXT NOT NULL,
    instrument_id UUID NOT NULL REFERENCES canonical_instruments(instrument_id),
    manifest_id UUID NOT NULL REFERENCES historical_raw_manifests(manifest_id),
    action_type TEXT NOT NULL CHECK (action_type IN ('BONUS','DIVIDEND','MERGER','RIGHTS','SPINOFF','SPLIT','SYMBOL_CHANGE','DELISTING','OTHER')),
    revision_number INTEGER NOT NULL CHECK (revision_number > 0),
    record_checksum TEXT NOT NULL CHECK (length(record_checksum) = 64),
    is_current BOOLEAN NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('ANNOUNCED','CONFIRMED','CANCELLED','REVISED')),
    supersedes_revision_id UUID REFERENCES corporate_action_revisions(action_revision_id),
    announcement_at TIMESTAMP,
    ex_date DATE,
    record_date DATE,
    pay_date DATE,
    original_terms JSONB NOT NULL,
    normalized_terms JSONB NOT NULL,
    available_at TIMESTAMP NOT NULL,
    ingested_at TIMESTAMP NOT NULL,
    UNIQUE (action_identity, revision_number),
    UNIQUE (action_identity, record_checksum)
);

CREATE UNIQUE INDEX corporate_action_current_idx
ON corporate_action_revisions(action_identity) WHERE is_current;

CREATE TABLE historical_quality_incidents (
    incident_id UUID PRIMARY KEY,
    manifest_id UUID NOT NULL REFERENCES historical_raw_manifests(manifest_id),
    record_type TEXT NOT NULL,
    natural_key TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    conflicting_revision_id UUID,
    quarantined_revision_id UUID NOT NULL,
    detected_at TIMESTAMP NOT NULL,
    UNIQUE (manifest_id, record_type, natural_key, quarantined_revision_id)
);

CREATE INDEX historical_mapping_lookup_idx
ON source_instrument_mappings(source_id, provider_exchange, provider_segment, provider_security_id, valid_from, valid_to);
CREATE INDEX historical_bar_lookup_idx
ON historical_bar_revisions(instrument_id, interval_code, bar_open_at, available_at);
CREATE INDEX corporate_action_lookup_idx
ON corporate_action_revisions(instrument_id, ex_date, available_at);
CREATE INDEX historical_quality_incident_idx
ON historical_quality_incidents(record_type, reason_code, detected_at);

CREATE FUNCTION reject_historical_raw_payload_update() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'historical raw payloads are immutable';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER historical_raw_payload_immutable
BEFORE UPDATE ON historical_raw_payloads
FOR EACH ROW EXECUTE FUNCTION reject_historical_raw_payload_update();

CREATE TRIGGER historical_raw_manifest_immutable
BEFORE UPDATE ON historical_raw_manifests
FOR EACH ROW EXECUTE FUNCTION reject_historical_raw_payload_update();
