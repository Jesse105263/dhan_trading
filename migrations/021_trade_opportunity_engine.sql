CREATE TABLE trade_opportunity_runs (
    run_id UUID PRIMARY KEY,
    model_version TEXT NOT NULL,
    source_run_ids JSONB NOT NULL,
    opportunity_count INTEGER NOT NULL CHECK (opportunity_count >= 0),
    eligible_count INTEGER NOT NULL CHECK (eligible_count >= 0),
    calculated_at TIMESTAMP NOT NULL,
    UNIQUE (model_version, source_run_ids)
);

CREATE TABLE trade_opportunities (
    opportunity_id UUID PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES trade_opportunity_runs(run_id) ON DELETE CASCADE,
    similarity_run_id UUID NOT NULL REFERENCES similarity_runs(run_id),
    query_vector_id UUID NOT NULL REFERENCES feature_store_vectors(vector_id),
    query_analytics_id UUID NOT NULL REFERENCES option_chain_analytics(analytics_id),
    query_ranking_id UUID REFERENCES option_rankings(ranking_id),
    underlying_symbol TEXT NOT NULL,
    expiry DATE NOT NULL,
    observed_at TIMESTAMP NOT NULL,
    model_version TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('ELIGIBLE','INSUFFICIENT_EVIDENCE','NO_OPPORTUNITY')),
    direction TEXT CHECK (direction IN ('LONG')),
    rank_position INTEGER NOT NULL CHECK (rank_position > 0),
    opportunity_score NUMERIC,
    evidence_quality NUMERIC NOT NULL CHECK (evidence_quality BETWEEN 0 AND 1),
    match_count INTEGER NOT NULL CHECK (match_count >= 0),
    classified_count INTEGER NOT NULL CHECK (classified_count >= 0),
    entry_zone_low NUMERIC,
    entry_zone_high NUMERIC,
    stop_zone NUMERIC,
    target_zones JSONB NOT NULL,
    expected_value NUMERIC,
    historical_win_rate NUMERIC,
    risk_reward NUMERIC,
    reasons_for JSONB NOT NULL,
    reasons_against JSONB NOT NULL,
    UNIQUE (run_id, similarity_run_id),
    UNIQUE (run_id, rank_position)
);

CREATE TABLE trade_opportunity_evidence (
    opportunity_id UUID NOT NULL REFERENCES trade_opportunities(opportunity_id) ON DELETE CASCADE,
    similarity_match_id UUID NOT NULL REFERENCES similarity_matches(match_id),
    matched_vector_id UUID NOT NULL REFERENCES feature_store_vectors(vector_id),
    matched_outcome_id UUID NOT NULL REFERENCES historical_outcomes(outcome_id),
    PRIMARY KEY (opportunity_id, similarity_match_id)
);

CREATE INDEX trade_opportunities_rank_idx ON trade_opportunities(state, opportunity_score DESC, rank_position);
CREATE INDEX trade_opportunity_evidence_idx ON trade_opportunity_evidence(opportunity_id);
