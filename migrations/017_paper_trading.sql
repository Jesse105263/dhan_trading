CREATE TABLE IF NOT EXISTS paper_trade_orders (
    order_id UUID PRIMARY KEY,
    signal_id UUID NOT NULL REFERENCES option_signals(signal_id) ON DELETE RESTRICT,
    source_run_id UUID NOT NULL REFERENCES option_chain_runs(run_id) ON DELETE RESTRICT,
    side VARCHAR(4) NOT NULL,
    quantity INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL,
    requested_at TIMESTAMP NOT NULL,
    filled_at TIMESTAMP,
    reference_run_id UUID REFERENCES option_chain_runs(run_id) ON DELETE RESTRICT,
    reference_price NUMERIC(18,6),
    fill_price NUMERIC(18,6),
    rejection_code VARCHAR(60),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_paper_trade_orders_side CHECK (side IN ('BUY','SELL')),
    CONSTRAINT ck_paper_trade_orders_status CHECK (status IN ('FILLED','REJECTED')),
    CONSTRAINT ck_paper_trade_orders_quantity CHECK (quantity > 0),
    CONSTRAINT ck_paper_trade_orders_result CHECK (
        (status = 'FILLED' AND filled_at IS NOT NULL AND reference_run_id IS NOT NULL
         AND reference_price > 0 AND fill_price > 0 AND rejection_code IS NULL)
        OR
        (status = 'REJECTED' AND filled_at IS NULL AND reference_run_id IS NULL
         AND reference_price IS NULL AND fill_price IS NULL AND rejection_code IS NOT NULL)
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_paper_trade_entry_order_signal
ON paper_trade_orders(signal_id) WHERE side = 'BUY' AND status = 'FILLED';

CREATE UNIQUE INDEX IF NOT EXISTS uq_paper_trade_exit_order_signal
ON paper_trade_orders(signal_id) WHERE side = 'SELL' AND status = 'FILLED';

CREATE TABLE IF NOT EXISTS paper_positions (
    position_id UUID PRIMARY KEY,
    signal_id UUID NOT NULL UNIQUE REFERENCES option_signals(signal_id) ON DELETE RESTRICT,
    signal_run_id UUID NOT NULL REFERENCES option_signal_runs(signal_run_id) ON DELETE RESTRICT,
    risk_run_id UUID NOT NULL REFERENCES option_risk_assessment_runs(risk_run_id) ON DELETE RESTRICT,
    assessment_id UUID NOT NULL REFERENCES option_risk_assessments(assessment_id) ON DELETE RESTRICT,
    selection_id UUID NOT NULL REFERENCES option_contract_selections(selection_id) ON DELETE RESTRICT,
    ranking_id UUID NOT NULL REFERENCES option_rankings(ranking_id) ON DELETE RESTRICT,
    analytics_id UUID NOT NULL REFERENCES option_chain_analytics(analytics_id) ON DELETE RESTRICT,
    source_run_id UUID NOT NULL REFERENCES option_chain_runs(run_id) ON DELETE RESTRICT,
    entry_order_id UUID NOT NULL UNIQUE REFERENCES paper_trade_orders(order_id) ON DELETE RESTRICT,
    exit_order_id UUID UNIQUE REFERENCES paper_trade_orders(order_id) ON DELETE RESTRICT,
    underlying_symbol VARCHAR(30) NOT NULL,
    expiry DATE NOT NULL,
    option_type VARCHAR(2) NOT NULL,
    security_id VARCHAR(30) NOT NULL,
    trading_symbol VARCHAR(120) NOT NULL,
    status VARCHAR(20) NOT NULL,
    quantity INTEGER NOT NULL,
    entry_run_id UUID NOT NULL REFERENCES option_chain_runs(run_id) ON DELETE RESTRICT,
    entry_time TIMESTAMP NOT NULL,
    entry_price NUMERIC(18,6) NOT NULL,
    latest_mark_run_id UUID NOT NULL REFERENCES option_chain_runs(run_id) ON DELETE RESTRICT,
    latest_mark_time TIMESTAMP NOT NULL,
    latest_mark_price NUMERIC(18,6) NOT NULL,
    exit_run_id UUID REFERENCES option_chain_runs(run_id) ON DELETE RESTRICT,
    exit_time TIMESTAMP,
    exit_price NUMERIC(18,6),
    gross_pnl NUMERIC(18,2) NOT NULL,
    transaction_costs NUMERIC(18,2) NOT NULL,
    net_pnl NUMERIC(18,2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT ck_paper_positions_type CHECK (option_type IN ('CE','PE')),
    CONSTRAINT ck_paper_positions_status CHECK (status IN ('OPEN','CLOSED')),
    CONSTRAINT ck_paper_positions_values CHECK (
        quantity > 0 AND entry_price > 0 AND latest_mark_price > 0 AND transaction_costs >= 0
    ),
    CONSTRAINT ck_paper_positions_exit CHECK (
        (status = 'OPEN' AND exit_order_id IS NULL AND exit_run_id IS NULL
         AND exit_time IS NULL AND exit_price IS NULL)
        OR
        (status = 'CLOSED' AND exit_order_id IS NOT NULL AND exit_run_id IS NOT NULL
         AND exit_time IS NOT NULL AND exit_price > 0)
    )
);

CREATE INDEX IF NOT EXISTS idx_paper_positions_status
ON paper_positions(status, updated_at DESC);

CREATE TABLE IF NOT EXISTS paper_trade_fills (
    fill_id UUID PRIMARY KEY,
    order_id UUID NOT NULL UNIQUE REFERENCES paper_trade_orders(order_id) ON DELETE RESTRICT,
    position_id UUID NOT NULL REFERENCES paper_positions(position_id) ON DELETE RESTRICT,
    side VARCHAR(4) NOT NULL,
    quantity INTEGER NOT NULL,
    reference_run_id UUID NOT NULL REFERENCES option_chain_runs(run_id) ON DELETE RESTRICT,
    reference_price NUMERIC(18,6) NOT NULL,
    fill_price NUMERIC(18,6) NOT NULL,
    filled_at TIMESTAMP NOT NULL,
    transaction_cost NUMERIC(18,2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_paper_trade_fills_side CHECK (side IN ('BUY','SELL')),
    CONSTRAINT ck_paper_trade_fills_values CHECK (
        quantity > 0 AND reference_price > 0 AND fill_price > 0 AND transaction_cost >= 0
    )
);

CREATE TABLE IF NOT EXISTS paper_position_events (
    event_id UUID PRIMARY KEY,
    position_id UUID NOT NULL REFERENCES paper_positions(position_id) ON DELETE RESTRICT,
    sequence_number INTEGER NOT NULL,
    event_type VARCHAR(20) NOT NULL,
    occurred_at TIMESTAMP NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_paper_position_event_sequence UNIQUE (position_id, sequence_number),
    CONSTRAINT ck_paper_position_event_type CHECK (event_type IN ('OPENED','MARKED','CLOSED')),
    CONSTRAINT ck_paper_position_event_sequence CHECK (sequence_number > 0)
);

CREATE INDEX IF NOT EXISTS idx_paper_position_events_position
ON paper_position_events(position_id, sequence_number);
