CREATE TABLE similarity_models_v2 (
    model_version TEXT PRIMARY KEY,
    policy_checksum TEXT NOT NULL CHECK(length(policy_checksum)=64),
    feature_schema_version TEXT NOT NULL REFERENCES feature_schema_versions_v2(schema_version),
    compatible_outcome_model TEXT,
    policy JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE similarity_runs_v2 (
    run_id UUID PRIMARY KEY,
    model_version TEXT NOT NULL REFERENCES similarity_models_v2(model_version),
    query_vector_id UUID NOT NULL REFERENCES feature_vectors_v2(vector_id),
    query_observed_at TIMESTAMP NOT NULL,
    cutoff_at TIMESTAMP NOT NULL,
    policy_checksum TEXT NOT NULL CHECK(length(policy_checksum)=64),
    candidate_count INTEGER NOT NULL CHECK(candidate_count>=0),
    match_count INTEGER NOT NULL CHECK(match_count>=0),
    evidence_state TEXT NOT NULL CHECK(evidence_state IN ('SUFFICIENT','INSUFFICIENT_EVIDENCE')),
    quality_metrics JSONB NOT NULL,
    lineage_checksum TEXT NOT NULL CHECK(length(lineage_checksum)=64),
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP NOT NULL,
    UNIQUE(model_version,query_vector_id,cutoff_at,policy_checksum)
);

CREATE TABLE similarity_matches_v2 (
    match_id UUID PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES similarity_runs_v2(run_id),
    rank_position INTEGER NOT NULL CHECK(rank_position>0),
    matched_vector_id UUID NOT NULL REFERENCES feature_vectors_v2(vector_id),
    matched_outcome_id UUID REFERENCES historical_outcomes_v2(outcome_id),
    distance NUMERIC NOT NULL CHECK(distance>=0),
    similarity_score NUMERIC NOT NULL CHECK(similarity_score>=0 AND similarity_score<=1),
    evidence_quality_score NUMERIC NOT NULL CHECK(evidence_quality_score>=0 AND evidence_quality_score<=1),
    shared_feature_count INTEGER NOT NULL CHECK(shared_feature_count>0),
    feature_diagnostics JSONB NOT NULL,
    filter_diagnostics JSONB NOT NULL,
    lineage_checksum TEXT NOT NULL CHECK(length(lineage_checksum)=64),
    UNIQUE(run_id,rank_position),
    UNIQUE(run_id,matched_vector_id)
);

CREATE INDEX similarity_v2_query_idx ON similarity_runs_v2(query_vector_id,cutoff_at);
CREATE INDEX similarity_v2_match_idx ON similarity_matches_v2(run_id,rank_position);

CREATE FUNCTION reject_similarity_v2_mutation() RETURNS trigger AS $$ BEGIN RAISE EXCEPTION 'Similarity Engine V2 evidence is immutable'; END; $$ LANGUAGE plpgsql;
CREATE TRIGGER similarity_runs_v2_immutable BEFORE UPDATE OR DELETE ON similarity_runs_v2 FOR EACH ROW EXECUTE FUNCTION reject_similarity_v2_mutation();
CREATE TRIGGER similarity_matches_v2_immutable BEFORE UPDATE OR DELETE ON similarity_matches_v2 FOR EACH ROW EXECUTE FUNCTION reject_similarity_v2_mutation();
