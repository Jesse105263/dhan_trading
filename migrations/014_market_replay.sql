CREATE TABLE IF NOT EXISTS market_replay_runs (
    replay_run_id UUID PRIMARY KEY,
    signal_run_id UUID NOT NULL REFERENCES option_signal_runs(signal_run_id) ON DELETE CASCADE,
    requested_as_of TIMESTAMP NOT NULL,
    replayed_at TIMESTAMP NOT NULL,
    signal_count INTEGER NOT NULL,
    event_count INTEGER NOT NULL,
    methodology_version VARCHAR(40) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_market_replay_run_counts CHECK (signal_count > 0 AND event_count > 0)
);

CREATE TABLE IF NOT EXISTS market_replay_events (
    replay_event_id UUID PRIMARY KEY,
    replay_run_id UUID NOT NULL REFERENCES market_replay_runs(replay_run_id) ON DELETE CASCADE,
    sequence_number INTEGER NOT NULL,
    event_type VARCHAR(40) NOT NULL,
    event_time TIMESTAMP NOT NULL,
    underlying_symbol VARCHAR(30) NOT NULL,
    expiry DATE NOT NULL,
    option_type VARCHAR(2),
    entity_id UUID NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_market_replay_sequence UNIQUE (replay_run_id, sequence_number),
    CONSTRAINT ck_market_replay_sequence CHECK (sequence_number > 0),
    CONSTRAINT ck_market_replay_event_type CHECK (event_type IN (
        'OPTION_CHAIN_CAPTURED','ANALYTICS_CALCULATED','RANKED',
        'CONTRACT_SELECTED','RISK_APPROVED','SIGNAL_GENERATED'
    )),
    CONSTRAINT ck_market_replay_option_type CHECK (option_type IS NULL OR option_type IN ('CE','PE'))
);

CREATE INDEX IF NOT EXISTS idx_market_replay_events_run_sequence
ON market_replay_events (replay_run_id, sequence_number);
