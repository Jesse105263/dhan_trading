CREATE TABLE feature_schema_versions_v2 (
    schema_version TEXT PRIMARY KEY,
    definition_checksum TEXT NOT NULL CHECK(length(definition_checksum)=64),
    compatible_schema_versions JSONB NOT NULL,
    compatible_outcome_models JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE feature_definitions_v2 (
    definition_id UUID PRIMARY KEY,
    schema_version TEXT NOT NULL REFERENCES feature_schema_versions_v2(schema_version),
    feature_name TEXT NOT NULL,
    feature_family TEXT NOT NULL,
    formula TEXT NOT NULL,
    missing_policy TEXT NOT NULL CHECK(missing_policy IN ('PRESERVE_NULL','REQUIRED','NOT_APPLICABLE')),
    normalization_policy TEXT NOT NULL CHECK(normalization_policy IN ('NONE','ZSCORE_TRAIN_WINDOW','MINMAX_TRAIN_WINDOW','LOG1P')),
    minimum_history INTEGER NOT NULL CHECK(minimum_history>0),
    description TEXT NOT NULL,
    definition_checksum TEXT NOT NULL CHECK(length(definition_checksum)=64),
    UNIQUE(schema_version,feature_name)
);

CREATE TABLE feature_materialization_runs_v2 (
    run_id UUID PRIMARY KEY,
    schema_version TEXT NOT NULL REFERENCES feature_schema_versions_v2(schema_version),
    as_of TIMESTAMP NOT NULL,
    definition_checksum TEXT NOT NULL CHECK(length(definition_checksum)=64),
    anchor_count INTEGER NOT NULL CHECK(anchor_count>=0),
    vector_count INTEGER NOT NULL CHECK(vector_count>=0),
    complete_count INTEGER NOT NULL CHECK(complete_count>=0),
    partial_count INTEGER NOT NULL CHECK(partial_count>=0),
    insufficient_count INTEGER NOT NULL CHECK(insufficient_count>=0),
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    UNIQUE(schema_version,as_of,definition_checksum)
);

CREATE TABLE feature_vectors_v2 (
    vector_id UUID PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES feature_materialization_runs_v2(run_id),
    schema_version TEXT NOT NULL REFERENCES feature_schema_versions_v2(schema_version),
    instrument_id UUID NOT NULL REFERENCES canonical_instruments(instrument_id),
    underlying_instrument_id UUID REFERENCES canonical_instruments(instrument_id),
    subject_type TEXT NOT NULL CHECK(subject_type IN ('UNDERLYING','FUTURE','OPTION')),
    anchor_bar_revision_id UUID NOT NULL REFERENCES historical_bar_revisions(bar_revision_id),
    anchor_manifest_id UUID NOT NULL REFERENCES historical_raw_manifests(manifest_id),
    interval_code TEXT NOT NULL,
    observed_at TIMESTAMP NOT NULL,
    available_at TIMESTAMP NOT NULL,
    quality_state TEXT NOT NULL CHECK(quality_state IN ('COMPLETE','PARTIAL','INSUFFICIENT')),
    feature_count INTEGER NOT NULL CHECK(feature_count>0),
    present_feature_count INTEGER NOT NULL CHECK(present_feature_count>=0),
    missing_feature_count INTEGER NOT NULL CHECK(missing_feature_count>=0),
    coverage_percentage NUMERIC NOT NULL CHECK(coverage_percentage>=0 AND coverage_percentage<=100),
    quality_metrics JSONB NOT NULL,
    definition_checksum TEXT NOT NULL CHECK(length(definition_checksum)=64),
    lineage_checksum TEXT NOT NULL CHECK(length(lineage_checksum)=64),
    materialized_at TIMESTAMP NOT NULL,
    CHECK(present_feature_count+missing_feature_count=feature_count),
    UNIQUE(anchor_bar_revision_id,schema_version)
);

CREATE TABLE feature_values_v2 (
    vector_id UUID NOT NULL REFERENCES feature_vectors_v2(vector_id),
    definition_id UUID NOT NULL REFERENCES feature_definitions_v2(definition_id),
    feature_name TEXT NOT NULL,
    numeric_value NUMERIC,
    missing_reason TEXT,
    source_revision_ids JSONB NOT NULL,
    value_checksum TEXT NOT NULL CHECK(length(value_checksum)=64),
    PRIMARY KEY(vector_id,definition_id),
    UNIQUE(vector_id,feature_name),
    CHECK((numeric_value IS NULL AND missing_reason IS NOT NULL) OR (numeric_value IS NOT NULL AND missing_reason IS NULL))
);

CREATE INDEX feature_vectors_v2_instrument_time_idx ON feature_vectors_v2(instrument_id,observed_at,schema_version);
CREATE INDEX feature_values_v2_name_idx ON feature_values_v2(feature_name,numeric_value,vector_id);

CREATE FUNCTION reject_feature_v2_update() RETURNS trigger AS $$ BEGIN RAISE EXCEPTION 'Feature Store V2 evidence is immutable'; END; $$ LANGUAGE plpgsql;
CREATE TRIGGER feature_vectors_v2_immutable BEFORE UPDATE OR DELETE ON feature_vectors_v2 FOR EACH ROW EXECUTE FUNCTION reject_feature_v2_update();
CREATE TRIGGER feature_values_v2_immutable BEFORE UPDATE OR DELETE ON feature_values_v2 FOR EACH ROW EXECUTE FUNCTION reject_feature_v2_update();
