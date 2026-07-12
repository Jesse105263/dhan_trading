CREATE TABLE IF NOT EXISTS option_backtest_runs (
    backtest_run_id UUID PRIMARY KEY,
    signal_run_id UUID NOT NULL REFERENCES option_signal_runs(signal_run_id) ON DELETE CASCADE,
    requested_as_of TIMESTAMP NOT NULL,
    calculated_at TIMESTAMP NOT NULL,
    signal_count INTEGER NOT NULL,
    completed_trade_count INTEGER NOT NULL,
    skipped_trade_count INTEGER NOT NULL,
    gross_pnl NUMERIC(18,2) NOT NULL,
    transaction_costs NUMERIC(18,2) NOT NULL,
    net_pnl NUMERIC(18,2) NOT NULL,
    return_on_exposure NUMERIC(12,8),
    win_rate NUMERIC(12,8),
    profit_factor NUMERIC(18,8),
    maximum_drawdown NUMERIC(18,2) NOT NULL,
    methodology_version VARCHAR(60) NOT NULL,
    parameters JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_option_backtest_run_counts CHECK (
        signal_count > 0 AND completed_trade_count >= 0 AND skipped_trade_count >= 0
        AND completed_trade_count + skipped_trade_count = signal_count
    ),
    CONSTRAINT ck_option_backtest_run_rates CHECK (
        return_on_exposure IS NULL OR return_on_exposure >= -1
    )
);

CREATE TABLE IF NOT EXISTS option_backtest_trades (
    backtest_trade_id UUID PRIMARY KEY,
    backtest_run_id UUID NOT NULL REFERENCES option_backtest_runs(backtest_run_id) ON DELETE CASCADE,
    signal_id UUID NOT NULL REFERENCES option_signals(signal_id) ON DELETE CASCADE,
    source_run_id UUID NOT NULL REFERENCES option_chain_runs(run_id) ON DELETE CASCADE,
    exit_run_id UUID REFERENCES option_chain_runs(run_id) ON DELETE SET NULL,
    underlying_symbol VARCHAR(30) NOT NULL,
    expiry DATE NOT NULL,
    option_type VARCHAR(2) NOT NULL,
    security_id VARCHAR(30) NOT NULL,
    trading_symbol VARCHAR(120) NOT NULL,
    quantity INTEGER NOT NULL,
    entry_time TIMESTAMP NOT NULL,
    exit_time TIMESTAMP,
    entry_reference_price NUMERIC(18,6) NOT NULL,
    entry_execution_price NUMERIC(18,6) NOT NULL,
    exit_reference_price NUMERIC(18,6),
    exit_execution_price NUMERIC(18,6),
    exit_reason VARCHAR(30) NOT NULL,
    gross_pnl NUMERIC(18,2) NOT NULL,
    transaction_costs NUMERIC(18,2) NOT NULL,
    net_pnl NUMERIC(18,2) NOT NULL,
    return_rate NUMERIC(12,8),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_option_backtest_trade_signal UNIQUE (backtest_run_id, signal_id),
    CONSTRAINT ck_option_backtest_trade_type CHECK (option_type IN ('CE','PE')),
    CONSTRAINT ck_option_backtest_trade_exit_reason CHECK (
        exit_reason IN ('TARGET','STOP_LOSS','LAST_AVAILABLE','NO_FUTURE_MARK')
    ),
    CONSTRAINT ck_option_backtest_trade_values CHECK (
        quantity > 0 AND entry_reference_price > 0 AND entry_execution_price > 0
    )
);

CREATE INDEX IF NOT EXISTS idx_option_backtest_runs_signal
ON option_backtest_runs (signal_run_id, calculated_at DESC);

CREATE INDEX IF NOT EXISTS idx_option_backtest_trades_run
ON option_backtest_trades (backtest_run_id, underlying_symbol, option_type);
