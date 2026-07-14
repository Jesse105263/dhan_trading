CREATE TABLE similarity_runs (
    run_id UUID PRIMARY KEY,
    query_vector_id UUID NOT NULL REFERENCES feature_store_vectors(vector_id),
    query_analytics_id UUID NOT NULL REFERENCES option_chain_analytics(analytics_id),
    query_ranking_id UUID REFERENCES option_rankings(ranking_id),
    model_version TEXT NOT NULL,
    configuration JSONB NOT NULL,
    filters JSONB NOT NULL,
    result_limit INTEGER NOT NULL CHECK (result_limit BETWEEN 1 AND 100),
    candidate_count INTEGER NOT NULL CHECK (candidate_count >= 0),
    match_count INTEGER NOT NULL CHECK (match_count >= 0),
    evidence_state TEXT NOT NULL CHECK (evidence_state IN ('SUFFICIENT', 'INSUFFICIENT')),
    calculated_at TIMESTAMP NOT NULL,
    UNIQUE (query_vector_id, model_version, filters, result_limit)
);

CREATE TABLE similarity_matches (
    match_id UUID PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES similarity_runs(run_id) ON DELETE CASCADE,
    rank_position INTEGER NOT NULL CHECK (rank_position > 0),
    matched_vector_id UUID NOT NULL REFERENCES feature_store_vectors(vector_id),
    matched_outcome_id UUID REFERENCES historical_outcomes(outcome_id),
    distance NUMERIC NOT NULL CHECK (distance >= 0),
    similarity_score NUMERIC NOT NULL CHECK (similarity_score BETWEEN 0 AND 1),
    shared_feature_count INTEGER NOT NULL CHECK (shared_feature_count >= 0),
    missing_feature_count INTEGER NOT NULL CHECK (missing_feature_count >= 0),
    feature_contributions JSONB NOT NULL,
    UNIQUE (run_id, rank_position),
    UNIQUE (run_id, matched_vector_id)
);

CREATE INDEX similarity_runs_query_idx ON similarity_runs(query_vector_id, calculated_at DESC);
CREATE INDEX similarity_matches_run_idx ON similarity_matches(run_id, rank_position);
