CREATE TABLE IF NOT EXISTS option_analytics_changes
(
    change_id UUID PRIMARY KEY,
    previous_analytics_id UUID NOT NULL
        REFERENCES option_chain_analytics(analytics_id) ON DELETE CASCADE,
    current_analytics_id UUID NOT NULL
        REFERENCES option_chain_analytics(analytics_id) ON DELETE CASCADE,
    previous_source_run_id UUID NOT NULL
        REFERENCES option_chain_runs(run_id) ON DELETE CASCADE,
    current_source_run_id UUID NOT NULL
        REFERENCES option_chain_runs(run_id) ON DELETE CASCADE,
    underlying_symbol VARCHAR(30) NOT NULL,
    expiry DATE NOT NULL,
    previous_captured_at TIMESTAMP NOT NULL,
    current_captured_at TIMESTAMP NOT NULL,
    calculated_at TIMESTAMP NOT NULL,
    elapsed_seconds BIGINT NOT NULL,
    spot_price_change NUMERIC(18, 6) NOT NULL,
    atm_straddle_change NUMERIC(18, 6) NOT NULL,
    total_call_oi_change BIGINT NOT NULL,
    total_put_oi_change BIGINT NOT NULL,
    total_pcr_change NUMERIC(18, 8),
    nearby_call_oi_change BIGINT NOT NULL,
    nearby_put_oi_change BIGINT NOT NULL,
    nearby_pcr_change NUMERIC(18, 8),
    atm_mean_iv_change NUMERIC(18, 6),
    nearby_mean_iv_change NUMERIC(18, 6),
    call_oi_wall_strike_change NUMERIC(18, 6),
    put_oi_wall_strike_change NUMERIC(18, 6),
    call_oi_wall_value_change BIGINT,
    put_oi_wall_value_change BIGINT,
    call_wall_changed BOOLEAN NOT NULL,
    put_wall_changed BOOLEAN NOT NULL,
    liquidity_coverage_change NUMERIC(18, 8) NOT NULL,
    price_coverage_change NUMERIC(18, 8) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_option_analytics_changes_current UNIQUE (current_analytics_id),
    CONSTRAINT uq_option_analytics_changes_pair UNIQUE
        (previous_analytics_id, current_analytics_id),
    CONSTRAINT ck_option_analytics_changes_distinct CHECK
        (previous_analytics_id <> current_analytics_id),
    CONSTRAINT ck_option_analytics_changes_elapsed CHECK
        (elapsed_seconds > 0)
);

CREATE INDEX IF NOT EXISTS
idx_option_analytics_changes_symbol_expiry_time
ON option_analytics_changes
(
    underlying_symbol,
    expiry,
    current_captured_at DESC
);
