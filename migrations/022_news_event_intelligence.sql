CREATE TABLE market_events (
    event_id UUID PRIMARY KEY,
    schema_version TEXT NOT NULL,
    source TEXT NOT NULL,
    source_event_id TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN ('CORPORATE_EARNINGS','CORPORATE_ACTION','EXCHANGE_ANNOUNCEMENT','MACROECONOMIC','RBI','SECTOR','MARKET_WIDE','COMPANY_NEWS')),
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    published_at TIMESTAMP,
    event_at TIMESTAMP,
    is_scheduled BOOLEAN NOT NULL,
    market_wide BOOLEAN NOT NULL,
    source_reference TEXT,
    event_metadata JSONB NOT NULL,
    sanitized_text TEXT NOT NULL,
    raw_source_checksum TEXT NOT NULL CHECK (length(raw_source_checksum)=64),
    deduplication_identity TEXT NOT NULL,
    ingested_at TIMESTAMP NOT NULL,
    CHECK (published_at IS NOT NULL OR event_at IS NOT NULL),
    UNIQUE (source, source_event_id),
    UNIQUE (deduplication_identity)
);

CREATE TABLE market_event_symbols (
    event_id UUID NOT NULL REFERENCES market_events(event_id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    PRIMARY KEY (event_id, symbol)
);

CREATE TABLE market_event_sectors (
    event_id UUID NOT NULL REFERENCES market_events(event_id) ON DELETE CASCADE,
    sector TEXT NOT NULL,
    PRIMARY KEY (event_id, sector)
);

CREATE TABLE market_event_vector_context (
    event_id UUID NOT NULL REFERENCES market_events(event_id) ON DELETE CASCADE,
    vector_id UUID NOT NULL REFERENCES feature_store_vectors(vector_id),
    outcome_id UUID REFERENCES historical_outcomes(outcome_id),
    context_type TEXT NOT NULL CHECK (context_type IN ('BEFORE_OBSERVATION','DURING_HOLDING','NEAR_EXPIRY')),
    predictive_eligible BOOLEAN NOT NULL,
    seconds_from_observation BIGINT,
    PRIMARY KEY (event_id, vector_id, context_type)
);

CREATE TABLE market_event_similarity_context (
    event_id UUID NOT NULL REFERENCES market_events(event_id) ON DELETE CASCADE,
    similarity_run_id UUID NOT NULL REFERENCES similarity_runs(run_id) ON DELETE CASCADE,
    query_vector_id UUID NOT NULL REFERENCES feature_store_vectors(vector_id),
    PRIMARY KEY (event_id, similarity_run_id)
);

CREATE TABLE market_event_opportunity_context (
    event_id UUID NOT NULL REFERENCES market_events(event_id) ON DELETE CASCADE,
    opportunity_id UUID NOT NULL REFERENCES trade_opportunities(opportunity_id) ON DELETE CASCADE,
    context_type TEXT NOT NULL CHECK (context_type IN ('RECENT_CONTEXT','UPCOMING_RISK')),
    seconds_from_observation BIGINT NOT NULL,
    PRIMARY KEY (event_id, opportunity_id, context_type)
);

CREATE INDEX market_events_time_idx ON market_events(COALESCE(event_at,published_at) DESC,event_id);
CREATE INDEX market_event_symbols_symbol_idx ON market_event_symbols(symbol,event_id);
CREATE INDEX market_event_sectors_sector_idx ON market_event_sectors(sector,event_id);
CREATE INDEX market_event_vector_idx ON market_event_vector_context(vector_id,context_type);
CREATE INDEX market_event_opportunity_idx ON market_event_opportunity_context(opportunity_id,context_type);
