CREATE TABLE outcome_model_versions_v2 (
    model_version TEXT PRIMARY KEY,
    policy_checksum TEXT NOT NULL CHECK(length(policy_checksum)=64),
    policy JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE outcome_materialization_runs_v2 (
    run_id UUID PRIMARY KEY,
    model_version TEXT NOT NULL REFERENCES outcome_model_versions_v2(model_version),
    as_of TIMESTAMP NOT NULL,
    policy_checksum TEXT NOT NULL CHECK(length(policy_checksum)=64),
    anchor_count INTEGER NOT NULL CHECK(anchor_count>=0),
    outcome_count INTEGER NOT NULL CHECK(outcome_count>=0),
    complete_count INTEGER NOT NULL CHECK(complete_count>=0),
    unknown_count INTEGER NOT NULL CHECK(unknown_count>=0),
    insufficient_count INTEGER NOT NULL CHECK(insufficient_count>=0),
    ambiguous_count INTEGER NOT NULL CHECK(ambiguous_count>=0),
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    UNIQUE(model_version,as_of,policy_checksum)
);

CREATE TABLE historical_outcomes_v2 (
    outcome_id UUID PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES outcome_materialization_runs_v2(run_id),
    model_version TEXT NOT NULL REFERENCES outcome_model_versions_v2(model_version),
    horizon_code TEXT NOT NULL,
    subject_type TEXT NOT NULL CHECK(subject_type IN ('UNDERLYING','OPTION')),
    instrument_id UUID NOT NULL REFERENCES canonical_instruments(instrument_id),
    underlying_instrument_id UUID REFERENCES canonical_instruments(instrument_id),
    anchor_bar_revision_id UUID NOT NULL REFERENCES historical_bar_revisions(bar_revision_id),
    terminal_bar_revision_id UUID REFERENCES historical_bar_revisions(bar_revision_id),
    entry_manifest_id UUID NOT NULL REFERENCES historical_raw_manifests(manifest_id),
    terminal_manifest_id UUID REFERENCES historical_raw_manifests(manifest_id),
    observed_at TIMESTAMP NOT NULL,
    available_at TIMESTAMP NOT NULL,
    horizon_end_at TIMESTAMP,
    terminal_at TIMESTAMP,
    outcome_state TEXT NOT NULL CHECK(outcome_state IN ('COMPLETE','UNKNOWN','INSUFFICIENT','AMBIGUOUS')),
    terminal_reason TEXT NOT NULL CHECK(terminal_reason IN ('TARGET','STOP','TIMEOUT','EXPIRY','MISSING_DATA','CORPORATE_ACTION','AMBIGUOUS_BARRIER')),
    missing_reason TEXT,
    corporate_action_count INTEGER NOT NULL CHECK(corporate_action_count>=0),
    entry_price NUMERIC,
    terminal_price NUMERIC,
    gross_return_pct NUMERIC,
    net_return_pct NUMERIC,
    maximum_favourable_excursion_pct NUMERIC,
    maximum_adverse_excursion_pct NUMERIC,
    maximum_drawdown_pct NUMERIC,
    realized_volatility_pct NUMERIC,
    volatility_adjusted_return NUMERIC,
    holding_duration_seconds BIGINT,
    path_observation_count INTEGER NOT NULL CHECK(path_observation_count>=0),
    target_return_pct NUMERIC,
    stop_return_pct NUMERIC,
    policy_checksum TEXT NOT NULL CHECK(length(policy_checksum)=64),
    lineage_checksum TEXT NOT NULL CHECK(length(lineage_checksum)=64),
    materialized_at TIMESTAMP NOT NULL,
    UNIQUE(anchor_bar_revision_id,model_version,horizon_code)
);

CREATE TABLE historical_outcome_path_v2 (
    outcome_id UUID NOT NULL REFERENCES historical_outcomes_v2(outcome_id),
    sequence_number INTEGER NOT NULL CHECK(sequence_number>0),
    bar_revision_id UUID NOT NULL REFERENCES historical_bar_revisions(bar_revision_id),
    manifest_id UUID NOT NULL REFERENCES historical_raw_manifests(manifest_id),
    bar_open_at TIMESTAMP NOT NULL,
    bar_close_at TIMESTAMP NOT NULL,
    available_at TIMESTAMP NOT NULL,
    PRIMARY KEY(outcome_id,sequence_number),
    UNIQUE(outcome_id,bar_revision_id)
);

CREATE INDEX outcome_v2_instrument_time_idx ON historical_outcomes_v2(instrument_id,observed_at,horizon_code);
CREATE INDEX outcome_v2_state_idx ON historical_outcomes_v2(outcome_state,model_version,horizon_code);

CREATE FUNCTION reject_outcome_v2_update() RETURNS trigger AS $$ BEGIN RAISE EXCEPTION 'Outcome V2 evidence is immutable'; END; $$ LANGUAGE plpgsql;
CREATE TRIGGER outcome_v2_immutable BEFORE UPDATE OR DELETE ON historical_outcomes_v2 FOR EACH ROW EXECUTE FUNCTION reject_outcome_v2_update();
CREATE TRIGGER outcome_v2_path_immutable BEFORE UPDATE OR DELETE ON historical_outcome_path_v2 FOR EACH ROW EXECUTE FUNCTION reject_outcome_v2_update();
