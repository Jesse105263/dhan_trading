CREATE TABLE IF NOT EXISTS option_signal_runs (
    signal_run_id UUID PRIMARY KEY,
    risk_run_id UUID NOT NULL REFERENCES option_risk_assessment_runs(risk_run_id) ON DELETE CASCADE,
    as_of TIMESTAMP NOT NULL,
    calculated_at TIMESTAMP NOT NULL,
    approved_input_count INTEGER NOT NULL,
    generated_signal_count INTEGER NOT NULL,
    methodology_version VARCHAR(40) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_option_signal_runs_risk UNIQUE (risk_run_id),
    CONSTRAINT ck_option_signal_run_counts CHECK (
        approved_input_count >= 0 AND generated_signal_count >= 0
    )
);

CREATE TABLE IF NOT EXISTS option_signals (
    signal_id UUID PRIMARY KEY,
    signal_run_id UUID NOT NULL REFERENCES option_signal_runs(signal_run_id) ON DELETE CASCADE,
    risk_run_id UUID NOT NULL REFERENCES option_risk_assessment_runs(risk_run_id) ON DELETE CASCADE,
    assessment_id UUID NOT NULL REFERENCES option_risk_assessments(assessment_id) ON DELETE CASCADE,
    selection_id UUID NOT NULL REFERENCES option_contract_selections(selection_id) ON DELETE CASCADE,
    ranking_id UUID NOT NULL REFERENCES option_rankings(ranking_id) ON DELETE CASCADE,
    analytics_id UUID NOT NULL REFERENCES option_chain_analytics(analytics_id) ON DELETE CASCADE,
    source_run_id UUID NOT NULL REFERENCES option_chain_runs(run_id) ON DELETE CASCADE,
    underlying_symbol VARCHAR(30) NOT NULL,
    expiry DATE NOT NULL,
    option_type VARCHAR(2) NOT NULL,
    security_id VARCHAR(30) NOT NULL,
    trading_symbol VARCHAR(120) NOT NULL,
    action VARCHAR(20) NOT NULL,
    direction VARCHAR(20) NOT NULL,
    strategy_context VARCHAR(30) NOT NULL,
    approved_lots INTEGER NOT NULL,
    approved_quantity INTEGER NOT NULL,
    entry_price NUMERIC(18,6) NOT NULL,
    premium_per_lot NUMERIC(18,6) NOT NULL,
    approved_exposure NUMERIC(18,2) NOT NULL,
    maximum_loss NUMERIC(18,2) NOT NULL,
    confidence_score NUMERIC(12,8) NOT NULL,
    rationale JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_option_signal_assessment UNIQUE (signal_run_id, assessment_id),
    CONSTRAINT ck_option_signal_type CHECK (option_type IN ('CE','PE')),
    CONSTRAINT ck_option_signal_action CHECK (action = 'BUY_TO_OPEN'),
    CONSTRAINT ck_option_signal_direction CHECK (direction IN ('BULLISH','BEARISH')),
    CONSTRAINT ck_option_signal_values CHECK (
        approved_lots > 0 AND approved_quantity > 0 AND entry_price > 0
        AND premium_per_lot > 0 AND approved_exposure > 0 AND maximum_loss > 0
        AND confidence_score BETWEEN 0 AND 1
    )
);

CREATE INDEX IF NOT EXISTS idx_option_signals_latest
ON option_signals (underlying_symbol, expiry, created_at DESC);
