CREATE TABLE IF NOT EXISTS option_ranking_runs (
    ranking_run_id UUID PRIMARY KEY,
    as_of TIMESTAMP NOT NULL,
    calculated_at TIMESTAMP NOT NULL,
    eligible_count INTEGER NOT NULL,
    methodology_version VARCHAR(30) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_option_ranking_runs_count CHECK (eligible_count >= 0)
);

CREATE TABLE IF NOT EXISTS option_rankings (
    ranking_id UUID PRIMARY KEY,
    ranking_run_id UUID NOT NULL REFERENCES option_ranking_runs(ranking_run_id) ON DELETE CASCADE,
    analytics_id UUID NOT NULL REFERENCES option_chain_analytics(analytics_id) ON DELETE CASCADE,
    change_id UUID NOT NULL REFERENCES option_analytics_changes(change_id) ON DELETE CASCADE,
    underlying_symbol VARCHAR(30) NOT NULL,
    expiry DATE NOT NULL,
    source_captured_at TIMESTAMP NOT NULL,
    rank_position INTEGER NOT NULL,
    total_score NUMERIC(12, 8) NOT NULL,
    liquidity_score NUMERIC(12, 8) NOT NULL,
    activity_score NUMERIC(12, 8) NOT NULL,
    volatility_score NUMERIC(12, 8) NOT NULL,
    directional_score NUMERIC(12, 8) NOT NULL,
    explanation JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_option_rankings_run_symbol UNIQUE (ranking_run_id, underlying_symbol, expiry),
    CONSTRAINT uq_option_rankings_run_rank UNIQUE (ranking_run_id, rank_position),
    CONSTRAINT ck_option_rankings_position CHECK (rank_position > 0),
    CONSTRAINT ck_option_rankings_scores CHECK (
        total_score BETWEEN 0 AND 1 AND liquidity_score BETWEEN 0 AND 1
        AND activity_score BETWEEN 0 AND 1 AND volatility_score BETWEEN 0 AND 1
        AND directional_score BETWEEN 0 AND 1
    )
);

CREATE INDEX IF NOT EXISTS idx_option_rankings_latest
ON option_rankings (underlying_symbol, expiry, source_captured_at DESC);
