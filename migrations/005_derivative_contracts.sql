CREATE TABLE IF NOT EXISTS derivative_contracts
(
    id BIGSERIAL PRIMARY KEY,
    exchange VARCHAR(20) NOT NULL,
    segment VARCHAR(30) NOT NULL,
    security_id VARCHAR(30) NOT NULL,
    trading_symbol VARCHAR(120) NOT NULL,
    underlying_symbol VARCHAR(30) NOT NULL,
    instrument_type VARCHAR(20) NOT NULL,
    expiry DATE NOT NULL,
    strike NUMERIC(18, 6),
    option_type VARCHAR(4),
    lot_size INTEGER NOT NULL,
    tick_size NUMERIC(18, 6) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    source_updated_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_derivative_contracts_dhan_identity
        UNIQUE (exchange, segment, security_id),

    CONSTRAINT ck_derivative_contracts_instrument_type
        CHECK (instrument_type IN ('FUTSTK', 'OPTSTK')),

    CONSTRAINT ck_derivative_contracts_option_type
        CHECK (
            (instrument_type = 'FUTSTK' AND option_type IS NULL AND strike IS NULL)
            OR
            (instrument_type = 'OPTSTK' AND option_type IN ('CE', 'PE') AND strike IS NOT NULL)
        ),

    CONSTRAINT ck_derivative_contracts_positive_lot_size
        CHECK (lot_size > 0),

    CONSTRAINT ck_derivative_contracts_positive_tick_size
        CHECK (tick_size > 0),

    CONSTRAINT ck_derivative_contracts_non_negative_strike
        CHECK (strike IS NULL OR strike >= 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS
idx_derivative_contracts_trading_symbol_unique
ON derivative_contracts(exchange, segment, trading_symbol);

CREATE INDEX IF NOT EXISTS
idx_derivative_contracts_active_underlying_expiry
ON derivative_contracts(underlying_symbol, expiry, instrument_type)
WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS
idx_derivative_contracts_active_expiry
ON derivative_contracts(expiry, underlying_symbol)
WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS
idx_derivative_contracts_option_chain
ON derivative_contracts(underlying_symbol, expiry, strike, option_type)
WHERE is_active = TRUE
  AND instrument_type = 'OPTSTK';

CREATE INDEX IF NOT EXISTS
idx_derivative_contracts_security_id
ON derivative_contracts(security_id);
