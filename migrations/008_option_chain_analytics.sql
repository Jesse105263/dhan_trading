CREATE TABLE IF NOT EXISTS option_chain_analytics
(
    analytics_id UUID PRIMARY KEY,
    source_run_id UUID NOT NULL
        REFERENCES option_chain_runs(run_id) ON DELETE CASCADE,
    underlying_symbol VARCHAR(30) NOT NULL,
    expiry DATE NOT NULL,
    source_captured_at TIMESTAMP NOT NULL,
    calculated_at TIMESTAMP NOT NULL,
    spot_price NUMERIC(18, 6) NOT NULL,
    atm_strike NUMERIC(18, 6) NOT NULL,
    atm_distance NUMERIC(18, 6) NOT NULL,
    atm_distance_pct NUMERIC(18, 8) NOT NULL,
    atm_call_price NUMERIC(18, 6) NOT NULL,
    atm_put_price NUMERIC(18, 6) NOT NULL,
    atm_straddle_cost NUMERIC(18, 6) NOT NULL,
    total_call_oi BIGINT NOT NULL,
    total_put_oi BIGINT NOT NULL,
    total_pcr NUMERIC(18, 8),
    nearby_call_oi BIGINT NOT NULL,
    nearby_put_oi BIGINT NOT NULL,
    nearby_pcr NUMERIC(18, 8),
    atm_call_iv NUMERIC(18, 6),
    atm_put_iv NUMERIC(18, 6),
    atm_mean_iv NUMERIC(18, 6),
    nearby_call_mean_iv NUMERIC(18, 6),
    nearby_put_mean_iv NUMERIC(18, 6),
    nearby_mean_iv NUMERIC(18, 6),
    call_oi_wall_strike NUMERIC(18, 6),
    call_oi_wall_value BIGINT,
    put_oi_wall_strike NUMERIC(18, 6),
    put_oi_wall_value BIGINT,
    minimum_strike NUMERIC(18, 6) NOT NULL,
    maximum_strike NUMERIC(18, 6) NOT NULL,
    strike_count INTEGER NOT NULL,
    nearby_strike_count INTEGER NOT NULL,
    quote_count INTEGER NOT NULL,
    priced_quote_count INTEGER NOT NULL,
    liquid_quote_count INTEGER NOT NULL,
    price_coverage NUMERIC(18, 8) NOT NULL,
    liquidity_coverage NUMERIC(18, 8) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_option_chain_analytics_source_run UNIQUE (source_run_id),
    CONSTRAINT ck_option_chain_analytics_non_negative_counts CHECK
    (
        strike_count > 0
        AND nearby_strike_count > 0
        AND quote_count > 0
        AND priced_quote_count >= 0
        AND liquid_quote_count >= 0
    ),
    CONSTRAINT ck_option_chain_analytics_coverage CHECK
    (
        price_coverage >= 0 AND price_coverage <= 1
        AND liquidity_coverage >= 0 AND liquidity_coverage <= 1
    )
);

CREATE INDEX IF NOT EXISTS
idx_option_chain_analytics_symbol_expiry_time
ON option_chain_analytics
(
    underlying_symbol,
    expiry,
    calculated_at DESC
);
