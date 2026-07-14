CREATE TABLE IF NOT EXISTS historical_outcomes (
    outcome_id UUID PRIMARY KEY,
    vector_id UUID NOT NULL REFERENCES feature_store_vectors(vector_id) ON DELETE CASCADE,
    analytics_id UUID NOT NULL REFERENCES option_chain_analytics(analytics_id) ON DELETE CASCADE,
    ranking_id UUID REFERENCES option_rankings(ranking_id) ON DELETE SET NULL,
    terminal_vector_id UUID REFERENCES feature_store_vectors(vector_id) ON DELETE SET NULL,
    underlying_symbol VARCHAR(30) NOT NULL,
    expiry DATE NOT NULL,
    observed_at TIMESTAMP NOT NULL,
    terminal_observed_at TIMESTAMP,
    model_version VARCHAR(40) NOT NULL,
    outcome_type VARCHAR(30) NOT NULL,
    entry_value NUMERIC,
    terminal_value NUMERIC,
    forward_return NUMERIC,
    maximum_favourable_excursion NUMERIC,
    maximum_adverse_excursion NUMERIC,
    holding_duration_seconds BIGINT,
    expiry_outcome NUMERIC,
    peak_gain NUMERIC,
    peak_loss NUMERIC,
    closing_return NUMERIC,
    won BOOLEAN,
    future_observation_count INTEGER NOT NULL,
    materialized_at TIMESTAMP NOT NULL,
    CONSTRAINT uq_historical_outcome_vector_version UNIQUE (vector_id, model_version),
    CONSTRAINT ck_historical_outcome_type CHECK
        (outcome_type IN ('NO_FUTURE_DATA', 'PARTIAL', 'EXPIRY_COMPLETE')),
    CONSTRAINT ck_historical_outcome_count CHECK (future_observation_count >= 0),
    CONSTRAINT ck_historical_outcome_terminal CHECK
        ((future_observation_count = 0 AND terminal_vector_id IS NULL AND terminal_observed_at IS NULL)
         OR (future_observation_count > 0 AND terminal_vector_id IS NOT NULL AND terminal_observed_at IS NOT NULL))
);

CREATE INDEX IF NOT EXISTS idx_historical_outcomes_symbol_expiry_time
ON historical_outcomes (underlying_symbol, expiry, observed_at DESC, outcome_id DESC);

CREATE INDEX IF NOT EXISTS idx_historical_outcomes_type
ON historical_outcomes (outcome_type, observed_at DESC);
