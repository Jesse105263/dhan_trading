CREATE TABLE IF NOT EXISTS instruments
(
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(30) UNIQUE NOT NULL,
    exchange VARCHAR(20),
    security_id VARCHAR(30),
    instrument_type VARCHAR(20),
    lot_size INTEGER,
    tick_size DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE instruments
ADD COLUMN IF NOT EXISTS exchange VARCHAR(20);

ALTER TABLE instruments
ADD COLUMN IF NOT EXISTS security_id VARCHAR(30);

ALTER TABLE instruments
ADD COLUMN IF NOT EXISTS instrument_type VARCHAR(20);

ALTER TABLE instruments
ADD COLUMN IF NOT EXISTS lot_size INTEGER;

ALTER TABLE instruments
ADD COLUMN IF NOT EXISTS tick_size DOUBLE PRECISION;

ALTER TABLE instruments
ADD COLUMN IF NOT EXISTS created_at
TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

CREATE UNIQUE INDEX IF NOT EXISTS
idx_instruments_symbol_unique
ON instruments(symbol);

CREATE INDEX IF NOT EXISTS
idx_instruments_exchange_security
ON instruments(exchange, security_id);


CREATE TABLE IF NOT EXISTS underlying_quotes
(
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(30) NOT NULL,
    spot_price DOUBLE PRECISION,
    volume BIGINT,
    oi BIGINT,
    timestamp TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS
idx_underlying_symbol_time
ON underlying_quotes(symbol, timestamp DESC);

CREATE INDEX IF NOT EXISTS
idx_underlying_timestamp
ON underlying_quotes(timestamp DESC);


CREATE TABLE IF NOT EXISTS option_quotes
(
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(30) NOT NULL,
    expiry DATE,
    strike DOUBLE PRECISION,
    option_type VARCHAR(5),
    ltp DOUBLE PRECISION,
    iv DOUBLE PRECISION,
    oi BIGINT,
    volume BIGINT,
    timestamp TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS
idx_option_symbol_expiry
ON option_quotes(symbol, expiry);


CREATE TABLE IF NOT EXISTS trade_signals
(
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(30),
    signal VARCHAR(30),
    confidence DOUBLE PRECISION,
    score DOUBLE PRECISION,
    strike DOUBLE PRECISION,
    premium DOUBLE PRECISION,
    stop_loss DOUBLE PRECISION,
    target1 DOUBLE PRECISION,
    target2 DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS pipeline_runs
(
    run_id VARCHAR(36) PRIMARY KEY,
    status VARCHAR(30) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    quote_timestamp TIMESTAMP,
    instrument_count INTEGER,
    snapshot_count INTEGER,
    feature_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE pipeline_runs
ADD COLUMN IF NOT EXISTS feature_count INTEGER;

CREATE INDEX IF NOT EXISTS
idx_pipeline_runs_started_at
ON pipeline_runs(started_at DESC);


CREATE TABLE IF NOT EXISTS scanner_snapshots
(
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(30),
    rank_score DOUBLE PRECISION,
    trade_score DOUBLE PRECISION,
    nearby_pcr DOUBLE PRECISION,
    atm_iv DOUBLE PRECISION,
    total_oi BIGINT,
    call_wall DOUBLE PRECISION,
    put_wall DOUBLE PRECISION,
    snapshot_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE scanner_snapshots
ADD COLUMN IF NOT EXISTS run_id VARCHAR(36);

ALTER TABLE scanner_snapshots
ADD COLUMN IF NOT EXISTS spot_price DOUBLE PRECISION;

ALTER TABLE scanner_snapshots
ADD COLUMN IF NOT EXISTS volume BIGINT;

ALTER TABLE scanner_snapshots
ADD COLUMN IF NOT EXISTS underlying_oi BIGINT;

ALTER TABLE scanner_snapshots
ADD COLUMN IF NOT EXISTS source_quote_timestamp TIMESTAMP;

CREATE UNIQUE INDEX IF NOT EXISTS
idx_scanner_snapshots_run_symbol
ON scanner_snapshots(run_id, symbol)
WHERE run_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS
idx_scanner_snapshots_time
ON scanner_snapshots(snapshot_time DESC);

CREATE INDEX IF NOT EXISTS
idx_scanner_snapshots_symbol_time
ON scanner_snapshots(symbol, snapshot_time DESC);


CREATE TABLE IF NOT EXISTS market_features
(
    id BIGSERIAL PRIMARY KEY,
    run_id VARCHAR(36) NOT NULL,
    symbol VARCHAR(30) NOT NULL,
    spot_price DOUBLE PRECISION NOT NULL,
    previous_spot_price DOUBLE PRECISION,
    price_change DOUBLE PRECISION,
    price_change_pct DOUBLE PRECISION,
    volume BIGINT,
    previous_volume BIGINT,
    volume_change BIGINT,
    volume_change_pct DOUBLE PRECISION,
    average_prior_volume DOUBLE PRECISION,
    relative_volume DOUBLE PRECISION,
    history_count INTEGER NOT NULL DEFAULT 0,
    calculated_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_market_features_run_symbol
        UNIQUE (run_id, symbol)
);

CREATE INDEX IF NOT EXISTS
idx_market_features_run
ON market_features(run_id);

CREATE INDEX IF NOT EXISTS
idx_market_features_symbol_time
ON market_features(symbol, calculated_at DESC);

CREATE INDEX IF NOT EXISTS
idx_market_features_relative_volume
ON market_features(relative_volume DESC);