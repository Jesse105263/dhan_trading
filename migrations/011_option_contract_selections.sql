CREATE TABLE IF NOT EXISTS option_contract_selection_runs (
    selection_run_id UUID PRIMARY KEY,
    ranking_run_id UUID NOT NULL REFERENCES option_ranking_runs(ranking_run_id) ON DELETE CASCADE,
    as_of TIMESTAMP NOT NULL,
    calculated_at TIMESTAMP NOT NULL,
    requested_underlying_count INTEGER NOT NULL,
    selected_contract_count INTEGER NOT NULL,
    methodology_version VARCHAR(30) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_option_selection_run_counts CHECK (requested_underlying_count >= 0 AND selected_contract_count >= 0)
);

CREATE TABLE IF NOT EXISTS option_contract_selections (
    selection_id UUID PRIMARY KEY,
    selection_run_id UUID NOT NULL REFERENCES option_contract_selection_runs(selection_run_id) ON DELETE CASCADE,
    ranking_id UUID NOT NULL REFERENCES option_rankings(ranking_id) ON DELETE CASCADE,
    analytics_id UUID NOT NULL REFERENCES option_chain_analytics(analytics_id) ON DELETE CASCADE,
    source_run_id UUID NOT NULL REFERENCES option_chain_runs(run_id) ON DELETE CASCADE,
    underlying_symbol VARCHAR(30) NOT NULL,
    expiry DATE NOT NULL,
    option_type VARCHAR(2) NOT NULL,
    security_id VARCHAR(30) NOT NULL,
    trading_symbol VARCHAR(120) NOT NULL,
    strike NUMERIC(18,6) NOT NULL,
    spot_price NUMERIC(18,6) NOT NULL,
    last_price NUMERIC(18,6) NOT NULL,
    bid_price NUMERIC(18,6),
    ask_price NUMERIC(18,6),
    open_interest BIGINT NOT NULL,
    volume BIGINT NOT NULL,
    lot_size INTEGER NOT NULL,
    distance_pct NUMERIC(18,8) NOT NULL,
    spread_pct NUMERIC(18,8),
    premium_per_lot NUMERIC(18,6) NOT NULL,
    contract_score NUMERIC(12,8) NOT NULL,
    explanation JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_option_contract_selection_side UNIQUE (selection_run_id, underlying_symbol, expiry, option_type),
    CONSTRAINT ck_option_contract_selection_type CHECK (option_type IN ('CE','PE')),
    CONSTRAINT ck_option_contract_selection_positive CHECK (strike >= 0 AND last_price > 0 AND open_interest >= 0 AND volume >= 0 AND lot_size > 0 AND premium_per_lot > 0),
    CONSTRAINT ck_option_contract_selection_score CHECK (contract_score BETWEEN 0 AND 1)
);

CREATE INDEX IF NOT EXISTS idx_option_contract_selections_latest
ON option_contract_selections (underlying_symbol, expiry, created_at DESC);
