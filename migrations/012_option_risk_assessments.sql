CREATE TABLE IF NOT EXISTS option_risk_assessment_runs (
    risk_run_id UUID PRIMARY KEY,
    selection_run_id UUID NOT NULL REFERENCES option_contract_selection_runs(selection_run_id) ON DELETE CASCADE,
    as_of TIMESTAMP NOT NULL,
    calculated_at TIMESTAMP NOT NULL,
    account_equity NUMERIC(18,2) NOT NULL,
    available_capital NUMERIC(18,2) NOT NULL,
    existing_total_exposure NUMERIC(18,2) NOT NULL,
    approved_contract_count INTEGER NOT NULL,
    rejected_contract_count INTEGER NOT NULL,
    approved_exposure NUMERIC(18,2) NOT NULL,
    methodology_version VARCHAR(40) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_option_risk_run_values CHECK (
        account_equity > 0 AND available_capital >= 0 AND existing_total_exposure >= 0
        AND approved_contract_count >= 0 AND rejected_contract_count >= 0 AND approved_exposure >= 0
    )
);

CREATE TABLE IF NOT EXISTS option_risk_assessments (
    assessment_id UUID PRIMARY KEY,
    risk_run_id UUID NOT NULL REFERENCES option_risk_assessment_runs(risk_run_id) ON DELETE CASCADE,
    selection_id UUID NOT NULL REFERENCES option_contract_selections(selection_id) ON DELETE CASCADE,
    selection_run_id UUID NOT NULL REFERENCES option_contract_selection_runs(selection_run_id) ON DELETE CASCADE,
    ranking_id UUID NOT NULL REFERENCES option_rankings(ranking_id) ON DELETE CASCADE,
    analytics_id UUID NOT NULL REFERENCES option_chain_analytics(analytics_id) ON DELETE CASCADE,
    source_run_id UUID NOT NULL REFERENCES option_chain_runs(run_id) ON DELETE CASCADE,
    underlying_symbol VARCHAR(30) NOT NULL,
    expiry DATE NOT NULL,
    option_type VARCHAR(2) NOT NULL,
    security_id VARCHAR(30) NOT NULL,
    trading_symbol VARCHAR(120) NOT NULL,
    premium_per_lot NUMERIC(18,6) NOT NULL,
    approved BOOLEAN NOT NULL,
    approved_lots INTEGER NOT NULL,
    approved_quantity INTEGER NOT NULL,
    approved_exposure NUMERIC(18,2) NOT NULL,
    maximum_loss NUMERIC(18,2) NOT NULL,
    rejection_code VARCHAR(60),
    explanation JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_option_risk_assessment_selection UNIQUE (risk_run_id, selection_id),
    CONSTRAINT ck_option_risk_assessment_values CHECK (
        premium_per_lot > 0 AND approved_lots >= 0 AND approved_quantity >= 0
        AND approved_exposure >= 0 AND maximum_loss >= 0
    ),
    CONSTRAINT ck_option_risk_assessment_approval CHECK (
        (approved = TRUE AND approved_lots > 0 AND approved_quantity > 0 AND approved_exposure > 0 AND rejection_code IS NULL)
        OR
        (approved = FALSE AND approved_lots = 0 AND approved_quantity = 0 AND approved_exposure = 0 AND maximum_loss = 0 AND rejection_code IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_option_risk_assessments_latest
ON option_risk_assessments (underlying_symbol, expiry, created_at DESC);
