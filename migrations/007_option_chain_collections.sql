CREATE TABLE IF NOT EXISTS option_chain_runs
(
    run_id UUID PRIMARY KEY,
    underlying_symbol VARCHAR(30) NOT NULL,
    underlying_security_id VARCHAR(30) NOT NULL,
    underlying_segment VARCHAR(30) NOT NULL,
    expiry DATE NOT NULL,
    status VARCHAR(20) NOT NULL,
    requested_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    spot_price NUMERIC(18, 6),
    strikes_received INTEGER NOT NULL DEFAULT 0,
    quotes_received INTEGER NOT NULL DEFAULT 0,
    quotes_inserted INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_option_chain_runs_status
        CHECK (status IN ('RUNNING', 'COMPLETED', 'FAILED')),
    CONSTRAINT ck_option_chain_runs_non_negative_counts
        CHECK (
            strikes_received >= 0
            AND quotes_received >= 0
            AND quotes_inserted >= 0
        )
);

CREATE INDEX IF NOT EXISTS
idx_option_chain_runs_symbol_expiry_time
ON option_chain_runs
(
    underlying_symbol,
    expiry,
    requested_at DESC
);

CREATE TABLE IF NOT EXISTS option_chain_quotes
(
    id BIGSERIAL PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES option_chain_runs(run_id) ON DELETE CASCADE,
    underlying_symbol VARCHAR(30) NOT NULL,
    expiry DATE NOT NULL,
    strike NUMERIC(18, 6) NOT NULL,
    option_type VARCHAR(2) NOT NULL,
    security_id VARCHAR(30),
    last_price NUMERIC(18, 6),
    implied_volatility NUMERIC(18, 6),
    open_interest BIGINT,
    volume BIGINT,
    bid_price NUMERIC(18, 6),
    ask_price NUMERIC(18, 6),
    captured_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_option_chain_quotes_run_contract
        UNIQUE (run_id, strike, option_type),
    CONSTRAINT ck_option_chain_quotes_option_type
        CHECK (option_type IN ('CE', 'PE')),
    CONSTRAINT ck_option_chain_quotes_non_negative_strike
        CHECK (strike >= 0),
    CONSTRAINT ck_option_chain_quotes_non_negative_oi
        CHECK (open_interest IS NULL OR open_interest >= 0),
    CONSTRAINT ck_option_chain_quotes_non_negative_volume
        CHECK (volume IS NULL OR volume >= 0)
);

CREATE INDEX IF NOT EXISTS
idx_option_chain_quotes_symbol_expiry_strike
ON option_chain_quotes
(
    underlying_symbol,
    expiry,
    strike,
    option_type
);

CREATE INDEX IF NOT EXISTS
idx_option_chain_quotes_captured_at
ON option_chain_quotes(captured_at DESC);
